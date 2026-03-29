import sqlite3


class SQLiteCriteriaMixin:

    def get_criterion(self, criterion_text: str) -> dict:
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

    def get_all_criteria(self) -> dict:
        try:
            self.cursor.execute("SELECT criterion_text, ai_verified FROM criteria")
            rows = self.cursor.fetchall()
            return {
                "criteria": [{"criterion_text": row[0], "ai_verified": bool(row[1])} for row in rows],
                "error": False,
            }
        except sqlite3.Error as e:
            return {"criteria": [], "error": True, "message": str(e)}

    def create_criterion_room(self, criterion_text: str, room_id: str, can_ai_verified: bool) -> dict:
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

    def get_all_criteria_room(self) -> dict:
        try:
            self.cursor.execute("SELECT criterion_text, room_id, can_ai_verified FROM criteria_room")
            rows = self.cursor.fetchall()
            return {
                "criteria_room": [
                    {"criterion_text": row[0], "room_id": row[1], "can_ai_verified": bool(row[2])}
                    for row in rows
                ],
                "error": False,
            }
        except sqlite3.Error as e:
            return {"criteria_room": [], "error": True, "message": str(e)}


class SACriteriaMixin:

    def get_criterion(self, criterion_text: str) -> dict:
        from ...models.orm import Criterion

        session = self.get_session()
        try:
            criterion = session.query(Criterion).filter(
                Criterion.criterion_text == criterion_text
            ).first()
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
        from ...models.orm import Criterion
        from sqlalchemy.exc import IntegrityError

        session = self.get_session()
        try:
            session.add(Criterion(criterion_text=criterion_text, ai_verified=ai_verified))
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

    def get_all_criteria(self) -> dict:
        from ...models.orm import Criterion

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

    def create_criterion_room(self, criterion_text: str, room_id: str, can_ai_verified: bool) -> dict:
        from ...models.orm import CriterionRoom
        from sqlalchemy.exc import IntegrityError

        session = self.get_session()
        try:
            session.add(CriterionRoom(
                criterion_text=criterion_text,
                room_id=room_id,
                can_ai_verified=can_ai_verified
            ))
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

    def get_all_criteria_room(self) -> dict:
        from ...models.orm import CriterionRoom

        session = self.get_session()
        try:
            records = session.query(CriterionRoom).all()
            return {
                "criteria_room": [
                    {"criterion_text": r.criterion_text, "room_id": r.room_id, "can_ai_verified": r.can_ai_verified}
                    for r in records
                ],
                "error": False,
            }
        except Exception as e:
            return {"criteria_room": [], "error": True, "message": str(e)}
        finally:
            session.close()
