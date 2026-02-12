"""
Менеджер базы данных для Backend проекта.
"""

import sqlite3
import os
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

        # Создание таблицы users
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')

        # Создание таблицы sessions для JWT токенов
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            user_agent TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

        # Создание индексов для оптимизации
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active, expires_at)')

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
            dict: Результат операции с полями message, error и user_id
        """
        from ..security.encryptors import hash_password

        if username is None:
            username = email.split('@')[0]

        password_hash = hash_password(password)

        try:
            self.cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            self.connection.commit()

            # Получить ID созданного пользователя
            user_id = self.cursor.lastrowid

            return {
                "message": "Пользователь зарегистрирован",
                "error": False,
                "user_id": user_id
            }
        except sqlite3.IntegrityError:
            return {"message": "Пользователь с таким email уже существует", "error": True}
        
    def check_user(self, email, password):
        """
        Проверить учетные данные пользователя.

        Args:
            email: Email пользователя
            password: Пароль пользователя

        Returns:
            dict: Результат проверки с полями message, error и user_id
        """
        from ..security.encryptors import verify_password

        try:
            self.cursor.execute(
                "SELECT id, password FROM users WHERE email = ?",
                (email,)
            )
            result = self.cursor.fetchone()

            if result is None:
                return {"message": f"Почта {email} не зарегистрирована", "error": True}

            user_id, stored_password = result

            # Проверка пароля через bcrypt
            if not verify_password(password, stored_password):
                return {"message": "Неверный пароль", "error": True}

            return {
                "message": "",
                "error": False,
                "user_id": user_id
            }

        except sqlite3.Error as e:
            return {"message": str(e), "error": True}
    
    def create_session(self, user_id: int, token: str, expires_at: str,
                       user_agent: str = None, ip_address: str = None) -> dict:
        """
        Создать новую сессию для пользователя.

        Args:
            user_id: ID пользователя
            token: JWT токен
            expires_at: Время истечения в ISO формате
            user_agent: User-Agent браузера
            ip_address: IP адрес клиента

        Returns:
            dict: {'session_id': int, 'error': bool}
        """
        try:
            self.cursor.execute("""
                INSERT INTO sessions (user_id, token, expires_at, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, token, expires_at, user_agent, ip_address))
            self.connection.commit()
            return {"session_id": self.cursor.lastrowid, "error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def validate_token(self, token: str) -> dict:
        """
        Проверить валидность токена.

        Args:
            token: JWT токен

        Returns:
            dict: {
                'valid': bool,
                'user_id': int|None,
                'session_id': int|None,
                'error': bool
            }
        """
        try:
            self.cursor.execute("""
                SELECT s.id, s.user_id, s.expires_at, u.email, u.username
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.is_active = 1
            """, (token,))

            result = self.cursor.fetchone()

            if result is None:
                return {"valid": False, "error": False, "message": "Токен не найден"}

            session_id, user_id, expires_at, email, username = result

            # Проверка истечения срока
            from datetime import datetime
            expires = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expires:
                # Деактивировать истекший токен
                self.revoke_token(token)
                return {"valid": False, "error": False, "message": "Токен истек"}

            return {
                "valid": True,
                "user_id": user_id,
                "session_id": session_id,
                "email": email,
                "username": username,
                "error": False
            }

        except sqlite3.Error as e:
            return {"valid": False, "error": True, "message": str(e)}

    def revoke_token(self, token: str) -> dict:
        """
        Отозвать токен (logout).

        Args:
            token: JWT токен

        Returns:
            dict: {'success': bool, 'error': bool, 'message': str}
        """
        try:
            self.cursor.execute("""
                UPDATE sessions
                SET is_active = 0
                WHERE token = ?
            """, (token,))
            self.connection.commit()

            if self.cursor.rowcount > 0:
                return {"success": True, "error": False, "message": "Токен успешно отозван"}
            else:
                return {"success": False, "error": False, "message": "Токен не найден"}

        except sqlite3.Error as e:
            return {"success": False, "error": True, "message": str(e)}

    @staticmethod
    def drop():
        """Удалить файл базы данных."""
        db_path = BackendPath('data/AppUsers.db')
        if os.path.exists(db_path):
            os.remove(db_path)