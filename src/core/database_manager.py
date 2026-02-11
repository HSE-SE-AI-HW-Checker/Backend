"""
Менеджер базы данных для Backend проекта.
"""

import sqlite3
import os
from ..security.encryptors import sha256
from ..utils.helpers import BackendPath


class DB:
    """Базовый класс для работы с базой данных."""
    
    def __init__(self):
        raise NotImplementedError()

    def execute(self, query):
        """
        Выполнить SQL запрос.
        
        Args:
            query: SQL запрос
        """
        raise NotImplementedError()

    def add_user(self, username, email, password):
        """
        Добавить пользователя в базу данных.
        
        Args:
            username: Имя пользователя
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            dict: Результат операции с полями message и error
        """
        raise NotImplementedError()

    def check_user(self, email, password):
        """
        Проверить учетные данные пользователя.
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            dict: Результат проверки с полями message и error
        """
        raise NotImplementedError()

    def drop(self):
        """Удалить базу данных."""
        raise NotImplementedError()


class SQLite(DB):
    """Реализация базы данных на SQLite."""
    
    def __init__(self):
        """Инициализация SQLite базы данных."""
        # Используем data/ директорию для хранения БД
        db_path = BackendPath('data/AppUsers.db')
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')
        self.connection.commit()

    def execute(self, query):
        """
        Выполнить SQL запрос.
        
        Args:
            query: SQL запрос
        """
        self.cursor.execute(query)
        self.connection.commit()

    def add_user(self, username, email, password):
        """
        Добавить пользователя в базу данных.
        
        Args:
            username: Имя пользователя (если None, используется часть email до @)
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            dict: Результат операции с полями message и error
        """
        if username is None:
            username = email.split('@')[0]

        password = sha256(password)
        try:
            self.execute(f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{password}')")
            return {"message": "Пользователь зарегистрирован", "error": False}
        except sqlite3.IntegrityError:
            return {"message": "Пользователь с таким email уже существует", "error": True}
        
    def check_user(self, email, password):
        """
        Проверить учетные данные пользователя.
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            dict: Результат проверки с полями message и error
        """
        password = sha256(password)
        self.execute(f"SELECT * FROM users WHERE email = '{email}'")
        if self.cursor.fetchone() is None:
            return {"message": f"Почта {email} не зарегистрирована", "error": True}
        

        self.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
        if self.cursor.fetchone() is None:
            return {"message": "Неверный пароль", "error": True}
        
        return {"message": "", "error": False}
    
    @staticmethod
    def drop():
        """Удалить файл базы данных."""
        db_path = BackendPath('data/AppUsers.db')
        if os.path.exists(db_path):
            os.remove(db_path)