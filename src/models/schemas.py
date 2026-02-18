from pydantic import BaseModel, Field
from typing import Optional, Dict

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
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None


class SignUpResponse(BaseModel):
    """Ответ на запрос регистрации."""
    message: str
    error: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None


class LogoutResponse(BaseModel):
    """Ответ на запрос выхода."""
    message: str
    success: bool


class SubmittedData(BaseModel):
    """Данные домашнего задания."""
    data: str
    # текст требования, тип требования (нужен ли мл для проверки?)
    requirements: Dict[str, int]
    data_type: int


class ModelResponse(BaseModel):
    """Модель ответа для генерации текста (non-streaming)."""
    
    text: str = Field(..., description="Сгенерированный текст")
    prompt: str = Field(..., description="Исходный промпт")