import uvicorn
import json
import importlib
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from util import get_from_config

ALIASES = {
    "--port": "port",
    "-p": "port",
    "-H": "host",
    "--host": "host"
}

# Модели Pydantic
class User(BaseModel):
    username: Optional[str] = None
    email: str
    password: str

class BasicMessage(BaseModel):
    message: str

class LogMessage(BaseModel):
    message: str

class AuthorizationResponse(BaseModel):
    message: str

class Submittion(BaseModel):
    data: str
    data_type: int

class Server:
    def __init__(self, args):
        self.config = 'default_config.json'
        for arg in args:
            name, val = arg.split("=")
            setattr(self, ALIASES.get(name, name), val)
        
        # Инициализация конфигурации, логгера и базы данных
        self._init_config_logger_db()
    
    def _init_config_logger_db(self):
        """Инициализация конфигурации, логгера и базы данных"""
        config_path = f"configs/{self.config}"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        logger_class = getattr(importlib.import_module("logs.loggers"), self.config.get("logger_implementation"))
        self.logger = logger_class(self.config.get("log_file"))
        
        db_class = getattr(importlib.import_module("databases"), self.config.get("database_implementation"))
        self.db = db_class()
        
        self.app = FastAPI()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков HTTP запросов"""
        
        @self.app.get("/health")
        async def health_check():
            """
            Проверка здоровья сервера
            """
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        
        @self.app.post("/log", response_model=BasicMessage)
        async def log(log_data: LogMessage):
            """
            Запись сообщения в лог
            """
            message = log_data.message
            print(message)
            self.logger.log(message)
            return {"message": "Сообщение записано в лог"}
        
        @self.app.post("/register", response_model=BasicMessage)
        async def register(user: User):
            """
            Регистрация пользователя
            """
            return self.db.add_user(user.username, user.email, user.password)

        @self.app.get("/authorize", response_model=BasicMessage)
        async def authorize(user: User):
            """
            Авторизация пользователя
            """
            return self.db.check_user(user.email, user.password)

    def run(self):
        uvicorn.run(
            self.app,
            host=getattr(self, 'host', self.config.get('host')),
            port=getattr(self, 'port', self.config.get('port')),
            reload=True
        )