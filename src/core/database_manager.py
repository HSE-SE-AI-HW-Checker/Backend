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
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
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

class SQLAlchemyDB(DB):
    """Реализация базы данных на SQLAlchemy."""

    def __init__(self, database_url=None):
        """
        Инициализация SQLAlchemy базы данных.
        
        Args:
            database_url: URL подключения к БД. Если None, берется из конфига.
        """
        from .database import get_engine, get_session_maker, Base
        from ..models.orm import User, Session
        from .config_manager import get_from_config

        if database_url is None:
            # Пытаемся получить URL из конфига, иначе используем дефолтный SQLite
            try:
                database_url = get_from_config("database_url")
            except AttributeError:
                # Fallback для обратной совместимости
                db_path = BackendPath('data/AppUsers.db')
                database_url = f"sqlite:///{db_path}"

        self.engine = get_engine(database_url)
        self.SessionLocal = get_session_maker(self.engine)
        
        # Создаем таблицы
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Получить сессию БД."""
        return self.SessionLocal()

    def add_user(self, username, email, password):
        """
        Добавить пользователя в базу данных.

        Args:
            username: Имя пользователя
            email: Email пользователя
            password: Пароль пользователя

        Returns:
            dict: Результат операции с полями message, error и user_id
        """
        from ..security.encryptors import hash_password
        from ..models.orm import User
        from sqlalchemy.exc import IntegrityError

        if username is None:
            username = email.split('@')[0]

        password_hash = hash_password(password)
        
        session = self.get_session()
        try:
            new_user = User(username=username, email=email, password=password_hash)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return {
                "message": "Пользователь зарегистрирован",
                "error": False,
                "user_id": new_user.id
            }
        except IntegrityError:
            session.rollback()
            return {"message": "Пользователь с таким email уже существует", "error": True}
        finally:
            session.close()

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
        from ..models.orm import User

        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()

            if user is None:
                return {"message": f"Почта {email} не зарегистрирована", "error": True}

            if not verify_password(password, user.password):
                return {"message": "Неверный пароль", "error": True}

            return {
                "message": "",
                "error": False,
                "user_id": user.id
            }
        finally:
            session.close()

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
        from ..models.orm import Session
        from datetime import datetime

        session = self.get_session()
        try:
            # Преобразуем строку ISO в datetime объект, если нужно
            # SQLAlchemy TIMESTAMP ожидает datetime объект
            if isinstance(expires_at, str):
                expires_dt = datetime.fromisoformat(expires_at)
            else:
                expires_dt = expires_at

            new_session = Session(
                user_id=user_id,
                token=token,
                expires_at=expires_dt,
                user_agent=user_agent,
                ip_address=ip_address
            )
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            return {"session_id": new_session.id, "error": False}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

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
        from ..models.orm import Session, User
        from datetime import datetime

        session = self.get_session()
        try:
            result = session.query(Session, User).join(User).filter(
                Session.token == token,
                Session.is_active == True
            ).first()

            if result is None:
                return {"valid": False, "error": False, "message": "Токен не найден"}

            db_session, user = result

            # Проверка истечения срока
            if datetime.utcnow() > db_session.expires_at:
                # Деактивировать истекший токен
                db_session.is_active = False
                session.commit()
                return {"valid": False, "error": False, "message": "Токен истек"}

            return {
                "valid": True,
                "user_id": user.id,
                "session_id": db_session.id,
                "email": user.email,
                "username": user.username,
                "error": False
            }

        except Exception as e:
            return {"valid": False, "error": True, "message": str(e)}
        finally:
            session.close()

    def revoke_token(self, token: str) -> dict:
        """
        Отозвать токен (logout).

        Args:
            token: JWT токен

        Returns:
            dict: {'success': bool, 'error': bool, 'message': str}
        """
        from ..models.orm import Session

        session = self.get_session()
        try:
            db_session = session.query(Session).filter(Session.token == token).first()

            if db_session:
                db_session.is_active = False
                session.commit()
                return {"success": True, "error": False, "message": "Токен успешно отозван"}
            else:
                return {"success": False, "error": False, "message": "Токен не найден"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": True, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def drop():
        """Удалить файл базы данных (если это SQLite файл)."""
        from .config_manager import get_from_config
        try:
            database_url = get_from_config("database_url")
            if database_url.startswith("sqlite:///"):
                path = database_url.replace("sqlite:///", "")
                if path != ":memory:" and os.path.exists(path):
                    os.remove(path)
        except AttributeError:
             # Fallback
            db_path = BackendPath('data/AppUsers.db')
            if os.path.exists(db_path):
                os.remove(db_path)