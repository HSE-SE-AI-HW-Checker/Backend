"""
Основной сервер Backend приложения.
"""

import uvicorn
import os
import signal
import importlib

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from src.utils.helpers import BackendPath, parse_submitted_data
from src.core.config_manager import get_ml_server_address
from src.models.config import ServerConfig
from src.services.ml_payload_bounds import utf8_payload_size_bytes
from src.services.orchestration_service import Orchestrator
from src.services.langgraph_orchestration_service import LangGraphOrchestrator
from src.security import get_current_user
from src.core.constants import DEFAULT_MOCK_RESPONSE
from src.models.schemas import (
    User, BasicMessage, LogMessage, SignInResponse, SignUpResponse,
    LogoutResponse, SubmittedData, ModelResponse
)

from src.app_routes import register_application_routes

ALIASES = {
    "--port": "port",
    "-p": "port",
    "-H": "host",
    "--host": "host"
}


class Server:
    """Основной класс сервера."""
    
    def __init__(self, arg: str):
        self.__init__(list(arg))

    def __init__(self, args: list):
        """
        Инициализация сервера.
        
        Args:
            args: Аргументы командной строки
        """
        self.config = 'default'
        for arg in args:
            if '=' not in arg:
                setattr(self, ALIASES.get(arg, arg), True)
                continue
            name, val = arg.split("=")
            setattr(self, ALIASES.get(name, name), val)
        
        self._init_config_logger_db()
    
    def _init_config_logger_db(self):
        """Инициализация конфигурации, логгера и базы данных."""
        load_dotenv(str(BackendPath('.env')))
        self.config = ServerConfig.from_config_name(self.config)
        
        from src.utils.logger import Logger
        self.logger = Logger(
            relative_file_path=self.config.log_file_path,
            mode=self.config.log_file_mode,
            to_console=self.config.log_to_console,
            log_level=self.config.log_level
        )
        
        db_class = getattr(importlib.import_module("src.core.database_manager"), self.config.database_implementation)
        if self.config.drop_db:
            db_class.drop()
        
        if self.config.database_implementation == "SQLAlchemyDB" and self.config.database_url:
            self.db = db_class(self.config.database_url)
        else:
            self.db = db_class()
        
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Сохраняем server instance в app.state для доступа в dependencies
        self.app.state.server = self

        self._setup_handlers()

    def _setup_handlers(self):
        """Настройка обработчиков HTTP запросов."""

        @self.app.get("/health")
        async def health_check():
            """
            Проверка здоровья сервера.
            
            Returns:
                dict: Статус сервера
            """
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }

        @self.app.post("/log", response_model=BasicMessage)
        async def log(log_data: LogMessage):
            """
            Запись сообщения в лог.
            
            Args:
                log_data: Данные для логирования
                
            Returns:
                dict: Подтверждение записи
            """
            message = log_data.message
            self.logger.log(message)
            return {"message": "Сообщение записано в лог"}
        
        @self.app.post("/sign_up", response_model=SignUpResponse)
        async def sign_up(user: User, request: Request):
            """
            Регистрация пользователя с возвратом JWT токенов.

            Args:
                user: Данные пользователя
                request: Request объект для получения IP и User-Agent

            Returns:
                dict: Результат регистрации с токенами
            """
            from ..security.encryptors import create_tokens_pair

            # Регистрируем пользователя
            result = self.db.add_user(user.username, user.email, user.password)

            if result["error"]:
                return result

            # Если регистрация успешна - создаем токены
            user_id = result.get("user_id")

            # Создаем пару токенов
            tokens = create_tokens_pair(
                user_id=user_id,
                email=user.email,
                secret_key=self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
                access_expire_minutes=self.config.jwt_access_token_expire_minutes,
                refresh_expire_days=self.config.jwt_refresh_token_expire_days
            )

            # Сохраняем access token в БД
            expires_at = (datetime.now() + timedelta(
                minutes=self.config.jwt_access_token_expire_minutes
            )).isoformat()

            user_agent = request.headers.get("user-agent")
            ip_address = request.client.host if request.client else None

            self.db.create_session(
                user_id=user_id,
                token=tokens["access_token"],
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address
            )

            # Возвращаем результат с токенами
            return {
                "message": result["message"],
                "error": False,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"]
            }

        @self.app.post("/sign_in", response_model=SignInResponse)
        async def sign_in(user: User, request: Request):
            """
            Авторизация пользователя с возвратом JWT токенов.

            Args:
                user: Данные пользователя
                request: Request объект

            Returns:
                dict: Результат авторизации с токенами
            """
            from ..security.encryptors import create_tokens_pair

            # Проверяем учетные данные
            result = self.db.check_user(user.email, user.password)

            if result["error"]:
                return result

            # Если вход успешен - создаем токены
            user_id = result.get("user_id")

            # Создаем пару токенов
            tokens = create_tokens_pair(
                user_id=user_id,
                email=user.email,
                secret_key=self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
                access_expire_minutes=self.config.jwt_access_token_expire_minutes,
                refresh_expire_days=self.config.jwt_refresh_token_expire_days
            )

            # Сохраняем access token в БД
            expires_at = (datetime.now() + timedelta(
                minutes=self.config.jwt_access_token_expire_minutes
            )).isoformat()

            user_agent = request.headers.get("user-agent")
            ip_address = request.client.host if request.client else None

            self.db.create_session(
                user_id=user_id,
                token=tokens["access_token"],
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address
            )

            # Возвращаем результат с токенами
            return {
                "message": "",
                "error": False,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"]
            }
        
        @self.app.post("/logout", response_model=LogoutResponse)
        async def logout(request: Request):
            """
            Выход из системы (отзыв токена).

            Args:
                request: Request объект с токеном в заголовке

            Returns:
                dict: Результат операции
            """
            # Извлекаем токен из заголовка
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return {
                    "message": "Отсутствует токен авторизации",
                    "success": False
                }

            token = auth_header.split(" ")[1]

            # Отзываем токен
            result = self.db.revoke_token(token)

            return {
                "message": result.get("message", "Выход выполнен"),
                "success": result.get("success", False)
            }

        @self.app.get("/me", summary="[dev only] Получить профиль текущего пользователя")
        async def get_profile(current_user: dict = Depends(get_current_user)):
            """
            Получить профиль текущего пользователя.

            Args:
                current_user: Текущий пользователь из токена

            Returns:
                dict: Информация о пользователе
            """
            return {
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "username": current_user["username"]
            }

        @self.app.post("/submit", response_model=ModelResponse)
        async def submit(submitted_data: SubmittedData, current_user: dict = Depends(get_current_user)):
            """
            Отправка домашнего задания (защищенный эндпоинт).

            Args:
                homework_data: Данные домашнего задания
                current_user: Текущий пользователь из токена

            Returns:
                dict: Ответ от ML сервера
            """

            project_data = parse_submitted_data(submitted_data)
            if not project_data:
                return ModelResponse(text=DEFAULT_MOCK_RESPONSE)

            size_bytes = utf8_payload_size_bytes(project_data)
            max_bytes = int(getattr(self.config, 'ml_input_max_bytes', 0) or 0)
            if max_bytes > 0 and size_bytes > max_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Объём текста проекта после нормализации ({size_bytes} байт) "
                        f"превышает допустимый лимит ({max_bytes} байт)."
                    ),
                )

            warn_frac = float(getattr(self.config, 'ml_input_warn_fraction', 0.5) or 0.0)
            if max_bytes > 0 and warn_frac > 0:
                warn_threshold = max(1, int(max_bytes * warn_frac))
                if size_bytes >= warn_threshold:
                    self.logger.log(
                        f"WARNING: объём входных текстовых данных для модели {size_bytes} байт "
                        f"(лимит {max_bytes}). Возможна нехватка контекста; при сбоях стоит увеличить n_ctx или сократить проект."
                    )

            ml_url = get_ml_server_address()
            try:
                orchestrator_primary = LangGraphOrchestrator(ml_url)
                response = orchestrator_primary.audit(submitted_data.requirements, project_data)
            except Exception as exc:
                self.logger.log(f"LangGraph audit failed, fallback to Orchestrator: {exc}")
                legacy_orchestrator = Orchestrator(ml_url)
                response = legacy_orchestrator.audit(submitted_data.requirements, project_data)

            return ModelResponse(text=response)

        register_application_routes(self)

    def run(self):
        """Запустить сервер."""
        uvicorn.run(
            self.app,
            host=getattr(self, 'host', self.config.host),
            port=getattr(self, 'port', self.config.port),
            reload=True
        )

    def stop(self):
        """Остановить сервер."""
        if self.config.drop_db:
            self.db.drop()

        os.kill(os.getpid(), signal.SIGINT)