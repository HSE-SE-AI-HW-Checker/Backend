"""
Настройка базы данных SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Базовый класс для моделей
Base = declarative_base()

def get_engine(database_url: str):
    """
    Создать engine для подключения к БД.
    
    Args:
        database_url: URL подключения
        
    Returns:
        Engine: Объект engine SQLAlchemy
    """
    connect_args = {}
    poolclass = None
    
    if "sqlite" in database_url:
        connect_args = {"check_same_thread": False}
        if ":memory:" in database_url:
            poolclass = StaticPool
        
    return create_engine(
        database_url,
        connect_args=connect_args,
        poolclass=poolclass
    )

def get_session_maker(engine):
    """
    Создать фабрику сессий.
    
    Args:
        engine: Объект engine SQLAlchemy
        
    Returns:
        sessionmaker: Фабрика сессий
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)