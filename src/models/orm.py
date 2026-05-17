"""
ORM модели базы данных (согласованы с core/db/*Mixin и SQLite-схемой main).
"""

import random
import string

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


def generate_room_id() -> str:
    """Генерация ID комнаты в формате XXXX-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    parts = ["".join(random.choices(chars, k=4)) for _ in range(3)]
    return "-".join(parts)


def generate_room_password() -> str:
    """Генерация пароля комнаты: 8 символов (буквы + цифры)."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=8))


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="creator", cascade="all, delete-orphan")


class Session(Base):
    """Модель сессии пользователя."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    expires_at = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    user = relationship("User", back_populates="sessions")


class Room(Base):
    """Комната: критерии хранятся в JSON (как в SQLite-ветке)."""

    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True, default=generate_room_id)
    name = Column(String(256), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False, default="")
    language = Column(String(64), nullable=False, default="")
    criteria = Column(JSON, nullable=False, default=list)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    participant_count = Column(Integer, nullable=False, default=0)
    password = Column(String(64), nullable=False, default="")

    creator = relationship("User", back_populates="rooms")


class RoomMember(Base):
    """Участник комнаты (таблица room_members)."""

    __tablename__ = "room_members"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    ai_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    owner_score = Column(Float, nullable=True)
    last_visit = Column(TIMESTAMP, nullable=False, server_default=func.now())
    submissions_count = Column(Integer, nullable=False, default=0)
    deadline = Column(TIMESTAMP, nullable=True)
    submission_url = Column(String, nullable=True)
    owner_comment = Column(String, nullable=True)


class Criterion(Base):
    """Глобальная таблица критериев (верификация AI)."""

    __tablename__ = "criteria"

    criterion_text = Column(String, primary_key=True)
    ai_verified = Column(Boolean, nullable=False, default=False)


class CriterionRoom(Base):
    """Связь критерий ↔ комната."""

    __tablename__ = "criteria_room"

    criterion_text = Column(
        String,
        ForeignKey("criteria.criterion_text", ondelete="CASCADE"),
        primary_key=True,
    )
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    can_ai_verified = Column(Boolean, nullable=False, default=False)


class Language(Base):
    """Доступные языки программирования."""

    __tablename__ = "languages"

    language = Column(String, primary_key=True)
