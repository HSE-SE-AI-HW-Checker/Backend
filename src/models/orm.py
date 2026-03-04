"""
ORM модели базы данных.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    TIMESTAMP,
    Text,
    UniqueConstraint,
)
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
    rooms_created = relationship("Room", back_populates="creator")


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
    """Учебная комната (задание, критерии, язык проекта)."""

    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=False, default="")
    language = Column(String(64), nullable=False)
    password_hash = Column(String(255), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    deadline = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    creator = relationship("User", back_populates="rooms_created")
    criteria = relationship(
        "RoomCriterion",
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="RoomCriterion.position",
    )
    memberships = relationship("RoomMembership", back_populates="room", cascade="all, delete-orphan")


class RoomCriterion(Base):
    """Критерий проверки внутри комнаты."""

    __tablename__ = "room_criteria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    ctype = Column(Integer, nullable=False, default=0)
    position = Column(Integer, nullable=False, default=0)

    room = relationship("Room", back_populates="criteria")


class RoomMembership(Base):
    """Участник комнаты."""

    __tablename__ = "room_memberships"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_membership"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    deadline_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(32), nullable=False, default="active")

    room = relationship("Room", back_populates="memberships")


class RoomVisit(Base):
    """Последнее посещение комнаты пользователем (для /rooms/recent)."""

    __tablename__ = "room_visits"
    __table_args__ = (UniqueConstraint("user_id", "room_id", name="uq_room_visit_user"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    last_visited = Column(TIMESTAMP, nullable=False, server_default=func.now())

    room = relationship("Room")