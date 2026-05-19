import sqlite3
import os

from ...utils.helpers import BackendPath
from .base import DB
from .users import SQLiteUsersMixin
from .sessions import SQLiteSessionsMixin
from .rooms import SQLiteRoomsMixin
from .criteria import SQLiteCriteriaMixin
from .languages import SQLiteLanguagesMixin
from .room_members import SQLiteRoomMembersMixin


class SQLite(SQLiteUsersMixin, SQLiteSessionsMixin, SQLiteRoomsMixin,
             SQLiteCriteriaMixin, SQLiteLanguagesMixin, SQLiteRoomMembersMixin, DB):
    """Реализация базы данных на SQLite."""

    def __init__(self):
        db_path = BackendPath('data/AppUsers.db')
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')

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

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active, expires_at)')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            language TEXT NOT NULL DEFAULT '',
            criteria TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            participant_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

        # Миграции таблицы rooms
        self.cursor.execute("PRAGMA table_info(rooms)")
        rooms_columns = {row[1] for row in self.cursor.fetchall()}
        if 'language' not in rooms_columns:
            self.cursor.execute("ALTER TABLE rooms ADD COLUMN language TEXT NOT NULL DEFAULT ''")
        if 'password' not in rooms_columns:
            from ...models.orm import generate_room_password
            self.cursor.execute("ALTER TABLE rooms ADD COLUMN password TEXT NOT NULL DEFAULT ''")
            # Проставляем пароль существующим комнатам
            self.cursor.execute("SELECT id FROM rooms WHERE password = ''")
            for (room_id,) in self.cursor.fetchall():
                self.cursor.execute(
                    "UPDATE rooms SET password = ? WHERE id = ?",
                    (generate_room_password(), room_id)
                )

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_rooms_creator_id ON rooms(creator_id)')

        # Миграция: пересоздать criteria если старая схема (с user_id или room_id)
        self.cursor.execute("PRAGMA table_info(criteria)")
        criteria_columns = {row[1] for row in self.cursor.fetchall()}
        if criteria_columns and ('user_id' in criteria_columns or 'room_id' in criteria_columns):
            self.cursor.execute("DROP TABLE IF EXISTS criteria_room")
            self.cursor.execute("DROP TABLE IF EXISTS criteria")

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS criteria (
            criterion_text TEXT PRIMARY KEY NOT NULL,
            ai_verified BOOLEAN NOT NULL DEFAULT 0
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS criteria_room (
            criterion_text TEXT NOT NULL,
            room_id TEXT NOT NULL,
            can_ai_verified BOOLEAN NOT NULL DEFAULT 0,
            PRIMARY KEY (criterion_text, room_id),
            FOREIGN KEY (criterion_text) REFERENCES criteria(criterion_text) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS languages (
            language TEXT PRIMARY KEY NOT NULL
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS room_members (
            user_id INTEGER NOT NULL,
            room_id TEXT NOT NULL,
            ai_score REAL,
            final_score REAL,
            owner_score REAL,
            last_visit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            submissions_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, room_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
        )''')

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_room_members_user_id ON room_members(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_room_members_room_id ON room_members(room_id)')

        # Миграция room_members: добавить новые колонки если нет
        self.cursor.execute("PRAGMA table_info(room_members)")
        rm_columns = {row[1] for row in self.cursor.fetchall()}
        if 'deadline' not in rm_columns:
            self.cursor.execute("ALTER TABLE room_members ADD COLUMN deadline TIMESTAMP")
        if 'submission_url' not in rm_columns:
            self.cursor.execute("ALTER TABLE room_members ADD COLUMN submission_url TEXT")
        if 'owner_comment' not in rm_columns:
            self.cursor.execute("ALTER TABLE room_members ADD COLUMN owner_comment TEXT")

        self.connection.commit()

    def execute(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    @staticmethod
    def drop():
        db_path = BackendPath('data/AppUsers.db')
        if os.path.exists(db_path):
            os.remove(db_path)
