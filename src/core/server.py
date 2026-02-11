"""
Основной сервер Backend приложения.
"""

import uvicorn
import os
import signal
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import requests

from ..utils.helpers import parse_homework_data
from ..core.config_manager import get_ml_server_address
from ..models.config import ServerConfig


ALIASES = {
    "--port": "port",
    "-p": "port",
    "-H": "host",
    "--host": "host"
}


class User(BaseModel):
    """Модель пользователя."""
    username: Optional[str] = None
    email: str
    password: str


class BasicMessage(BaseModel):
    """Базовое сообщение."""
    message: str


class LogMessage(BaseModel):
    """Сообщение для логирования."""
    message: str


class SignInResponse(BaseModel):
    """Ответ на запрос входа."""
    message: str
    error: bool


class SignUpResponse(BaseModel):
    """Ответ на запрос регистрации."""
    message: str
    error: bool


class HomeworkData(BaseModel):
    """Данные домашнего задания."""
    data: str
    data_type: int


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
        self.config = ServerConfig.from_config_name(self.config)
        
        logger_class = getattr(importlib.import_module("src.utils.logger"), self.config.logger_implementation)
        self.logger = logger_class(self.config.log_file_path)
        
        db_class = getattr(importlib.import_module("src.core.database_manager"), self.config.database_implementation)
        if self.config.drop_db:
            db_class.drop()
        self.db = db_class()
        
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
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
        async def sign_up(user: User):
            """
            Регистрация пользователя.
            
            Args:
                user: Данные пользователя
                
            Returns:
                dict: Результат регистрации
            """
            return self.db.add_user(user.username, user.email, user.password)

        @self.app.post("/sign_in", response_model=SignInResponse)
        async def sign_in(user: User):
            """
            Авторизация пользователя.
            
            Args:
                user: Данные пользователя
                
            Returns:
                dict: Результат авторизации
            """
            return self.db.check_user(user.email, user.password)
        
        @self.app.post("/submit", response_model=BasicMessage)
        async def submit(homework_data: HomeworkData):
            """
            Отправка данных на сервер.
            
            Args:
                homework_data: Данные домашнего задания
                
            Returns:
                dict: Ответ от ML сервера
            """
            # TODO: Как-то обработать
            parse_homework_data(homework_data)

            response = requests.post(
                f'{get_ml_server_address()}/ask_ai',
                json={
                    "prompt": homework_data.data,
                    "is_agent": False
                },
                headers={'Content-Type': 'application/json'}
            )

            return response.json()

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