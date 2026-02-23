"""
ORM модели базы данных.
"""

import random
import string

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


def generate_room_id() -> str:
    """Генерация ID комнаты в формате XXXX-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(random.choices(chars, k=4)) for _ in range(3)]
    return '-'.join(parts)

class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    # Связь с сессиями
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    # Связь с комнатами
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

    # Связь с пользователем
    user = relationship("User", back_populates="sessions")


class Room(Base):
    """Модель комнаты."""
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, default=generate_room_id)
    name = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    language = Column(String, nullable=False, default="")
    criteria = Column(JSON, nullable=False, default=list)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    participant_count = Column(Integer, nullable=False, default=0)

    # Связь с создателем
    creator = relationship("User", back_populates="rooms")


class Criterion(Base):
    """Модель критерия проверки."""
    __tablename__ = "criteria"

    criterion_text = Column(String, primary_key=True)
    ai_verified = Column(Boolean, nullable=False, default=False)


class Language(Base):
    """Доступный язык программирования."""
    __tablename__ = "languages"

    language = Column(String, primary_key=True)


class CriterionRoom(Base):
    """Связь критерия с комнатой."""
    __tablename__ = "criteria_room"

    criterion_text = Column(String, ForeignKey("criteria.criterion_text", ondelete="CASCADE"), primary_key=True)
    room_id = Column(String, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    can_ai_verified = Column(Boolean, nullable=False, default=False)