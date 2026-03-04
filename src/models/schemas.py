from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

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


# --- Комнаты и языки программирования (пояснительная записка) ---


class LanguageRow(BaseModel):
    id: str
    name: str
    extensions: List[str] = Field(default_factory=list)


class LanguagesOutResponse(BaseModel):
    languages: List[LanguageRow]


class CreateRoomRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    language: str = Field(..., min_length=1)
    criteria: List[str] = Field(..., min_length=1)
    password: str = Field(..., min_length=4)
    deadline: Optional[datetime] = None


class CreateRoomResponse(BaseModel):
    room_id: str
    name: str
    created_at: datetime


class CriteriaVerifyRequest(BaseModel):
    criteria_text: str = Field(..., min_length=1)


class CriteriaVerifyResponse(BaseModel):
    can_ai_verified: bool


class RoomListItem(BaseModel):
    id: str
    name: str
    description: str = ""
    created_at: datetime


class RecentRoomRow(BaseModel):
    id: str
    name: str
    last_visited: datetime


class CriterionItem(BaseModel):
    text: str
    type: int = 0


class RoomDetailOut(BaseModel):
    id: str
    name: str
    description: str = ""
    language: str
    criteria: List[CriterionItem] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    deadline: Optional[datetime] = None


class JoinRoomBody(BaseModel):
    password: str = Field(..., min_length=1)


class JoinRoomResponse(BaseModel):
    success: bool
    message: str
    room: Optional[RoomDetailOut] = None


class MemberMeResponse(BaseModel):
    user_id: str
    joined_at: datetime
    deadline: Optional[datetime] = None
    status: str