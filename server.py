import uvicorn
import json
import os
import signal
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from util import parse_homework_data, BackendPath, get_ml_server_address

import requests

ALIASES = {
    "--port": "port",
    "-p": "port",
    "-H": "host",
    "--host": "host"
}

class User(BaseModel):
    username: Optional[str] = None
    email: str
    password: str

class BasicMessage(BaseModel):
    message: str

class LogMessage(BaseModel):
    message: str

class SignInResponse(BaseModel):
    message: str
    error: bool

class SignUpResponse(BaseModel):
    message: str
    error: bool

class HomeworkData(BaseModel):
    data: str
    data_type: int

class Server:
    def __init__(self, arg: str):
        self.__init__(self, list(arg))

    def __init__(self, args: list):
        self.config = 'default_config.json'
        for arg in args:
            if '=' not in arg:
                setattr(self, ALIASES.get(arg, arg), True)
                continue
            name, val = arg.split("=")
            setattr(self, ALIASES.get(name, name), val)
        
        self._init_config_logger_db()
    
    def _init_config_logger_db(self):
        config_path = BackendPath(f"configs/{self.config}")
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        for key, value in self.config.items():
            setattr(self, key, value)
        
        logger_class = getattr(importlib.import_module("logs.loggers"), self.logger_implementation)
        self.logger = logger_class(self.log_file_path)
        
        db_class = getattr(importlib.import_module("databases"), self.database_implementation)
        if self.drop_db:
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
            self.logger.log(message)
            return {"message": "Сообщение записано в лог"}
        
        @self.app.post("/sign_up", response_model=SignUpResponse)
        async def sign_up(user: User):
            """
            Регистрация пользователя
            """
            return self.db.add_user(user.username, user.email, user.password)

        @self.app.post("/sign_in", response_model=SignInResponse)
        async def sign_in(user: User):
            """
            Авторизация пользователя
            """
            return self.db.check_user(user.email, user.password)
        
        @self.app.post("/submit", response_model=BasicMessage)
        async def submit(homework_data: HomeworkData):
            """
            Отправка данных на сервер
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
        uvicorn.run(
            self.app,
            host=getattr(self, 'host', self.config.get('host')),
            port=getattr(self, 'port', self.config.get('port')),
            reload=True
        )

    def stop(self):
        if self.drop_db:
            self.db.drop()

        os.kill(os.getpid(), signal.SIGINT)