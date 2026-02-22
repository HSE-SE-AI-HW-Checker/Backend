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

        # Создание таблицы rooms
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            criteria TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            participant_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_rooms_creator_id ON rooms(creator_id)')

        # Миграция: пересоздать criteria если старая схема (с user_id или room_id)
        self.cursor.execute("PRAGMA table_info(criteria)")
        criteria_columns = {row[1] for row in self.cursor.fetchall()}
        if criteria_columns and ('user_id' in criteria_columns or 'room_id' in criteria_columns):
            self.cursor.execute("DROP TABLE IF EXISTS criteria_room")
            self.cursor.execute("DROP TABLE IF EXISTS criteria")

        # Создание таблицы criteria
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS criteria (
            criterion_text TEXT PRIMARY KEY NOT NULL,
            ai_verified BOOLEAN NOT NULL DEFAULT 0
        )''')

        # Создание таблицы criteria_room
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS criteria_room (
            criterion_text TEXT NOT NULL,
            room_id TEXT NOT NULL,
            can_ai_verified BOOLEAN NOT NULL DEFAULT 0,
            PRIMARY KEY (criterion_text, room_id),
            FOREIGN KEY (criterion_text) REFERENCES criteria(criterion_text) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
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

    def create_room(self, creator_id: int, name: str, description: str = "",
                    criteria: list = None) -> dict:
        """Создать комнату."""
        import json
        from ..models.orm import generate_room_id

        room_id = generate_room_id()
        criteria_json = json.dumps(criteria or [], ensure_ascii=False)

        try:
            self.cursor.execute("""
                INSERT INTO rooms (id, name, creator_id, description, criteria)
                VALUES (?, ?, ?, ?, ?)
            """, (room_id, name, creator_id, description, criteria_json))
            self.connection.commit()
            return {"room_id": room_id, "error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_room(self, room_id: str) -> dict:
        """Получить комнату по ID."""
        import json

        try:
            self.cursor.execute("""
                SELECT id, name, creator_id, description, criteria, created_at, participant_count
                FROM rooms WHERE id = ?
            """, (room_id,))
            result = self.cursor.fetchone()

            if result is None:
                return {"error": True, "message": "Комната не найдена"}

            return {
                "room": {
                    "id": result[0],
                    "name": result[1],
                    "creator_id": result[2],
                    "description": result[3],
                    "criteria": json.loads(result[4]),
                    "created_at": result[5],
                    "participant_count": result[6]
                },
                "error": False
            }
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_user_rooms(self, user_id: int) -> dict:
        """Получить все комнаты пользователя."""
        import json

        try:
            self.cursor.execute("""
                SELECT id, name, creator_id, description, criteria, created_at, participant_count
                FROM rooms WHERE creator_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = self.cursor.fetchall()

            rooms = [
                {
                    "id": row[0],
                    "name": row[1],
                    "creator_id": row[2],
                    "description": row[3],
                    "criteria": json.loads(row[4]),
                    "created_at": row[5],
                    "participant_count": row[6]
                }
                for row in rows
            ]
            return {"rooms": rooms, "error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def delete_room(self, room_id: str) -> dict:
        """Удалить комнату."""
        try:
            self.cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return {"success": True, "error": False, "message": "Комната удалена"}
            return {"success": False, "error": False, "message": "Комната не найдена"}
        except sqlite3.Error as e:
            return {"success": False, "error": True, "message": str(e)}

    def get_criterion(self, criterion_text: str) -> dict:
        """Получить критерий по тексту."""
        try:
            self.cursor.execute(
                "SELECT criterion_text, ai_verified FROM criteria WHERE criterion_text = ?",
                (criterion_text,)
            )
            row = self.cursor.fetchone()
            if row is None:
                return {"criterion": None, "error": False}
            return {"criterion": {"criterion_text": row[0], "ai_verified": bool(row[1])}, "error": False}
        except sqlite3.Error as e:
            return {"criterion": None, "error": True, "message": str(e)}

    def create_criterion(self, criterion_text: str, ai_verified: bool) -> dict:
        """Создать критерий."""
        try:
            self.cursor.execute(
                "INSERT INTO criteria (criterion_text, ai_verified) VALUES (?, ?)",
                (criterion_text, ai_verified)
            )
            self.connection.commit()
            return {"error": False}
        except sqlite3.IntegrityError as e:
            msg = str(e)
            if "UNIQUE" in msg or "PRIMARY KEY" in msg:
                return {"error": True, "message": "Такой критерий уже существует"}
            return {"error": True, "message": f"Ошибка схемы БД: {msg}. Пересоздайте базу данных."}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def create_criterion_room(self, criterion_text: str, room_id: str, can_ai_verified: bool) -> dict:
        """Создать запись в таблице criteria_room."""
        try:
            self.cursor.execute(
                "INSERT INTO criteria_room (criterion_text, room_id, can_ai_verified) VALUES (?, ?, ?)",
                (criterion_text, room_id, can_ai_verified)
            )
            self.connection.commit()
            return {"error": False}
        except sqlite3.IntegrityError as e:
            return {"error": True, "message": str(e)}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_all_criteria(self) -> dict:
        """Получить все критерии."""
        try:
            self.cursor.execute("SELECT criterion_text, ai_verified FROM criteria")
            rows = self.cursor.fetchall()
            return {
                "criteria": [{"criterion_text": row[0], "ai_verified": bool(row[1])} for row in rows],
                "error": False,
            }
        except sqlite3.Error as e:
            return {"criteria": [], "error": True, "message": str(e)}

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

        # Миграция: пересоздать criteria если старая схема (с user_id или room_id)
        from sqlalchemy import inspect, text
        inspector = inspect(self.engine)
        if 'criteria' in inspector.get_table_names():
            existing_columns = {col['name'] for col in inspector.get_columns('criteria')}
            if 'user_id' in existing_columns or 'room_id' in existing_columns:
                with self.engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS criteria_room"))
                    conn.execute(text("DROP TABLE IF EXISTS criteria"))
                    conn.commit()

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

    def create_room(self, creator_id: int, name: str, description: str = "",
                    criteria: list = None) -> dict:
        """Создать комнату."""
        from ..models.orm import Room

        session = self.get_session()
        try:
            new_room = Room(
                name=name,
                creator_id=creator_id,
                description=description,
                criteria=criteria or []
            )
            session.add(new_room)
            session.commit()
            session.refresh(new_room)
            return {"room_id": new_room.id, "error": False}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def get_room(self, room_id: str) -> dict:
        """Получить комнату по ID."""
        from ..models.orm import Room

        session = self.get_session()
        try:
            room = session.query(Room).filter(Room.id == room_id).first()

            if room is None:
                return {"error": True, "message": "Комната не найдена"}

            return {
                "room": {
                    "id": room.id,
                    "name": room.name,
                    "creator_id": room.creator_id,
                    "description": room.description,
                    "criteria": room.criteria,
                    "created_at": room.created_at.isoformat() if room.created_at else None,
                    "participant_count": room.participant_count
                },
                "error": False
            }
        finally:
            session.close()

    def get_user_rooms(self, user_id: int) -> dict:
        """Получить все комнаты пользователя."""
        from ..models.orm import Room

        session = self.get_session()
        try:
            rooms = session.query(Room).filter(Room.creator_id == user_id).order_by(Room.created_at.desc()).all()

            return {
                "rooms": [
                    {
                        "id": room.id,
                        "name": room.name,
                        "creator_id": room.creator_id,
                        "description": room.description,
                        "criteria": room.criteria,
                        "created_at": room.created_at.isoformat() if room.created_at else None,
                        "participant_count": room.participant_count
                    }
                    for room in rooms
                ],
                "error": False
            }
        except Exception as e:
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def delete_room(self, room_id: str) -> dict:
        """Удалить комнату."""
        from ..models.orm import Room

        session = self.get_session()
        try:
            room = session.query(Room).filter(Room.id == room_id).first()
            if room:
                session.delete(room)
                session.commit()
                return {"success": True, "error": False, "message": "Комната удалена"}
            return {"success": False, "error": False, "message": "Комната не найдена"}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": True, "message": str(e)}
        finally:
            session.close()

    def get_criterion(self, criterion_text: str) -> dict:
        """Получить критерий по тексту."""
        from ..models.orm import Criterion

        session = self.get_session()
        try:
            criterion = session.query(Criterion).filter(Criterion.criterion_text == criterion_text).first()
            if criterion is None:
                return {"criterion": None, "error": False}
            return {
                "criterion": {"criterion_text": criterion.criterion_text, "ai_verified": criterion.ai_verified},
                "error": False,
            }
        except Exception as e:
            return {"criterion": None, "error": True, "message": str(e)}
        finally:
            session.close()

    def create_criterion(self, criterion_text: str, ai_verified: bool) -> dict:
        """Создать критерий."""
        from ..models.orm import Criterion
        from sqlalchemy.exc import IntegrityError

        session = self.get_session()
        try:
            criterion = Criterion(criterion_text=criterion_text, ai_verified=ai_verified)
            session.add(criterion)
            session.commit()
            return {"error": False}
        except IntegrityError as e:
            session.rollback()
            msg = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
            if "unique" in msg.lower() or "primary key" in msg.lower() or "duplicate" in msg.lower():
                return {"error": True, "message": "Такой критерий уже существует"}
            return {"error": True, "message": f"Ошибка схемы БД: {msg}. Пересоздайте базу данных."}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def create_criterion_room(self, criterion_text: str, room_id: str, can_ai_verified: bool) -> dict:
        """Создать запись в таблице criteria_room."""
        from ..models.orm import CriterionRoom
        from sqlalchemy.exc import IntegrityError

        session = self.get_session()
        try:
            cr = CriterionRoom(criterion_text=criterion_text, room_id=room_id, can_ai_verified=can_ai_verified)
            session.add(cr)
            session.commit()
            return {"error": False}
        except IntegrityError as e:
            session.rollback()
            return {"error": True, "message": str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def get_all_criteria(self) -> dict:
        """Получить все критерии."""
        from ..models.orm import Criterion

        session = self.get_session()
        try:
            criteria = session.query(Criterion).all()
            return {
                "criteria": [{"criterion_text": c.criterion_text, "ai_verified": c.ai_verified} for c in criteria],
                "error": False,
            }
        except Exception as e:
            return {"criteria": [], "error": True, "message": str(e)}
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