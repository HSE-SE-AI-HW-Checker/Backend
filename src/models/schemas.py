from pydantic import BaseModel, Field
from typing import Optional, Dict, List

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


class Criterion(BaseModel):
    """Критерий проверки."""
    criterion_text: str = Field(..., min_length=1, description="Текст критерия (не может быть пустым)")
    is_ai_verified: bool


class RoomCreate(BaseModel):
    """Данные для создания комнаты."""
    name: str = Field(..., min_length=1, description="Название комнаты (не может быть пустым)")
    description: str = Field(..., min_length=1, description="Описание комнаты (не может быть пустым)")
    language: str = Field(..., min_length=1, description="Язык программирования (не может быть пустым)")
    criteria: List[Criterion] = Field(
        default=[],
        description=(
            "Список критериев проверки. Каждый элемент — объект с полями:\n"
            "- **criterion_text** (str): текст критерия;\n"
            "- **is_ai_verified** (bool): требует ли критерий проверки через AI "
            "(если true — критерий должен быть предварительно верифицирован через POST /criteria/verify)."
        )
    )


class RoomResponse(BaseModel):
    """Ответ с данными комнаты."""
    id: str
    name: str
    creator_id: int
    description: str
    language: str
    criteria: List[Criterion]
    created_at: str
    participant_count: int


class CriterionRecord(BaseModel):
    """Запись критерия из таблицы criteria."""
    criterion_text: str
    ai_verified: bool


class CriterionRoomRecord(BaseModel):
    """Запись из таблицы criteria_room."""
    criterion_text: str
    room_id: str
    can_ai_verified: bool


class CriterionVerifyRequest(BaseModel):
    """Запрос на верификацию критерия."""
    criterion_text: str = Field(..., min_length=1, description="Текст критерия (не может быть пустым)")


class CriterionVerifyResponse(BaseModel):
    """Ответ на верификацию критерия."""
    can_ai_verified: bool


class ModelResponse(BaseModel):
    """Модель ответа для генерации текста (non-streaming)."""

    text: str = Field(..., description="Сгенерированный текст")
    prompt: str = Field(..., description="Исходный промпт")