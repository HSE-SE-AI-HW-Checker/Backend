"""
ORM модели базы данных.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    # Связь с сессиями
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

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