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
        min_length=1,
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
    creator_name: str
    description: str
    language: str
    criteria: List[Criterion]
    created_at: str
    participant_count: int
    password: str


class JoinRoomRequest(BaseModel):
    """Запрос на вступление в комнату."""
    password: str = Field(..., min_length=1, description="Пароль комнаты")


class CriterionRecord(BaseModel):
    """Запись критерия из таблицы criteria."""
    criterion_text: str
    ai_verified: bool


class CriterionRoomRecord(BaseModel):
    """Запись из таблицы criteria_room."""
    criterion_text: str
    room_id: str
    can_ai_verified: bool


class LanguageCreate(BaseModel):
    """Запрос на добавление языка программирования."""
    language: str = Field(..., min_length=1, description="Название языка программирования")


class CriterionVerifyRequest(BaseModel):
    """Запрос на верификацию критерия."""
    criterion_text: str = Field(..., min_length=1, description="Текст критерия (не может быть пустым)")


class CriterionVerifyResponse(BaseModel):
    """Ответ на верификацию критерия."""
    can_ai_verified: bool


class OwnerScoreUpdate(BaseModel):
    """Запрос на обновление оценки владельца."""
    owner_score: float = Field(..., ge=0, le=100, description="Оценка от владельца комнаты (0–100)")


class ScoresUpdate(BaseModel):
    """[dev only] Запрос на обновление оценок участника комнаты."""
    ai_score: Optional[float] = Field(None, ge=0, le=100, description="Оценка от AI (0–100)")
    final_score: Optional[float] = Field(None, ge=0, le=100, description="Итоговая оценка (0–100)")
    owner_score: Optional[float] = Field(None, ge=0, le=100, description="Оценка от владельца (0–100)")
    deadline: Optional[str] = Field(None, description="Дедлайн ISO 8601, например 2026-06-01T23:59:00")
    submissions_count: Optional[int] = Field(None, ge=0, description="Количество отправленных решений")


class RoomMemberResponse(BaseModel):
    """Ответ с данными участника комнаты."""
    user_id: int
    room_id: str
    ai_score: Optional[float] = None
    final_score: Optional[float] = None
    owner_score: Optional[float] = None
    last_visit: str
    submissions_count: int
    deadline: Optional[str] = None


class RecentRoomResponse(BaseModel):
    """Недавняя комната пользователя (только ключевые поля)."""
    room_id: str
    room_name: str
    last_visit: str
    submissions_count: int
    participant_count: int
    final_score: Optional[float] = None


class ModelResponse(BaseModel):
    """Модель ответа для генерации текста (non-streaming)."""

    text: str = Field(..., description="Сгенерированный текст")
    prompt: str = Field(..., description="Исходный промпт")