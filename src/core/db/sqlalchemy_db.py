import os

from ...utils.helpers import BackendPath
from .base import DB
from .users import SAUsersMixin
from .sessions import SASessionsMixin
from .rooms import SARoomsMixin
from .criteria import SACriteriaMixin
from .languages import SALanguagesMixin
from .room_members import SARoomMembersMixin


class SQLAlchemyDB(SAUsersMixin, SASessionsMixin, SARoomsMixin,
                   SACriteriaMixin, SALanguagesMixin, SARoomMembersMixin, DB):
    """Реализация базы данных на SQLAlchemy."""

    def __init__(self, database_url=None):
        from ..database import get_engine, get_session_maker, Base
        from ..config_manager import get_from_config

        if database_url is None:
            try:
                database_url = get_from_config("database_url")
            except AttributeError:
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

        import src.models.orm  # noqa: F401 — регистрирует все модели в Base.metadata
        Base.metadata.create_all(bind=self.engine)

        # Миграции таблицы rooms
        inspector = inspect(self.engine)
        if 'rooms' in inspector.get_table_names():
            rooms_columns = {col['name'] for col in inspector.get_columns('rooms')}
            with self.engine.connect() as conn:
                if 'language' not in rooms_columns:
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN language TEXT NOT NULL DEFAULT ''"))
                if 'password' not in rooms_columns:
                    from ...models.orm import generate_room_password
                    conn.execute(text("ALTER TABLE rooms ADD COLUMN password TEXT NOT NULL DEFAULT ''"))
                    # Проставляем пароль существующим комнатам
                    result = conn.execute(text("SELECT id FROM rooms WHERE password = ''"))
                    for (room_id,) in result.fetchall():
                        conn.execute(
                            text("UPDATE rooms SET password = :pwd WHERE id = :id"),
                            {"pwd": generate_room_password(), "id": room_id}
                        )
                conn.commit()

    def get_session(self):
        return self.SessionLocal()

    def execute(self, query):
        from sqlalchemy import text
        with self.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()

    @staticmethod
    def drop():
        from ..config_manager import get_from_config
        try:
            database_url = get_from_config("database_url")
            if database_url.startswith("sqlite:///"):
                path = database_url.replace("sqlite:///", "")
                if path != ":memory:" and os.path.exists(path):
                    os.remove(path)
        except AttributeError:
            db_path = BackendPath('data/AppUsers.db')
            if os.path.exists(db_path):
                os.remove(db_path)
