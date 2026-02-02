from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import importlib
from datetime import datetime
from logs.loggers import SimpleLogger

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

def setup_handlers(app: FastAPI, config="configs/default_config.json"):
    with open(config, 'r') as f:
        config = json.load(f)
        logger = getattr(importlib.import_module("logs.loggers"), config.get("logger_implementation"))(config.get("log_file"))
        db = getattr(importlib.import_module("databases"), config.get("database_implementation"))()

    @app.get("/health")
    async def health_check():
        """
        Проверка здоровья сервера
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    @app.post("/log", response_model=BasicMessage)
    async def log(log_data: LogMessage):
        """
        Запись сообщения в лог
        """
        message = log_data.message
        print(message)
        logger.log(message)
        return {"message": "Сообщение записано в лог"}
    
    @app.post("/register", response_model=BasicMessage)
    async def register(user: User):
        """
        Регистрация пользователя
        """
        return db.add_user(user.username, user.email, user.password)

    @app.get("/authorize", response_model=BasicMessage)
    async def authorize(user: User):
        """
        Авторизация пользователя
        """
        return db.check_user(user.email, user.password)
