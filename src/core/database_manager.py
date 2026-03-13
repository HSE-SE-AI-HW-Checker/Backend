"""
Менеджер базы данных для Backend проекта.
"""

from .db import SQLite, SQLAlchemyDB

__all__ = ["SQLite", "SQLAlchemyDB"]
