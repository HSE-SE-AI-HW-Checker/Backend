import sqlite3


def _normalize_criteria(raw: list) -> list:
    """Привести критерии к формату [{criterion_text, is_ai_verified}], пропуская пустые."""
    result = []
    for c in raw:
        if isinstance(c, str):
            if c:
                result.append({"criterion_text": c, "is_ai_verified": False})
        else:
            if c.get("criterion_text"):
                result.append(c)
    return result


class SQLiteRoomsMixin:

    @staticmethod
    def _normalize_criteria(raw: list) -> list:
        return _normalize_criteria(raw)

    def create_room(self, creator_id: int, name: str, description: str = "",
                    language: str = "", criteria: list = None) -> dict:
        import json
        from ...models.orm import generate_room_id, generate_room_password

        room_id = generate_room_id()
        password = generate_room_password()
        criteria_json = json.dumps(criteria or [], ensure_ascii=False)

        try:
            self.cursor.execute("""
                INSERT INTO rooms (id, name, creator_id, description, language, criteria, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (room_id, name, creator_id, description, language, criteria_json, password))
            self.connection.commit()
            return {"room_id": room_id, "error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_room(self, room_id: str) -> dict:
        import json

        try:
            self.cursor.execute("""
                SELECT id, name, creator_id, description, language, criteria, created_at, participant_count, password
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
                    "language": result[4],
                    "criteria": _normalize_criteria(json.loads(result[5])),
                    "created_at": result[6],
                    "participant_count": result[7],
                    "password": result[8] or "",
                },
                "error": False
            }
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_user_rooms(self, user_id: int) -> dict:
        import json

        try:
            self.cursor.execute("""
                SELECT id, name, creator_id, description, language, criteria, created_at, participant_count, password
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
                    "language": row[4],
                    "criteria": _normalize_criteria(json.loads(row[5])),
                    "created_at": row[6],
                    "participant_count": row[7],
                    "password": row[8] or "",
                }
                for row in rows
            ]
            return {"rooms": rooms, "error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_all_user_rooms(self, user_id: int) -> dict:
        """Все комнаты пользователя: созданные им + те, в которые он вступил."""
        import json

        try:
            self.cursor.execute("""
                SELECT id, name, creator_id, description, language, criteria, created_at, participant_count, password
                FROM rooms WHERE creator_id = ?
                UNION
                SELECT r.id, r.name, r.creator_id, r.description, r.language, r.criteria,
                       r.created_at, r.participant_count, r.password
                FROM rooms r
                JOIN room_members rm ON r.id = rm.room_id
                WHERE rm.user_id = ? AND r.creator_id != ?
                ORDER BY created_at DESC
            """, (user_id, user_id, user_id))
            rows = self.cursor.fetchall()

            rooms = [
                {
                    "id": row[0],
                    "name": row[1],
                    "creator_id": row[2],
                    "description": row[3],
                    "language": row[4],
                    "criteria": _normalize_criteria(json.loads(row[5])),
                    "created_at": row[6],
                    "participant_count": row[7],
                    "password": row[8] or "",
                }
                for row in rows
            ]
            return {"rooms": rooms, "error": False}
        except sqlite3.Error as e:
            return {"rooms": [], "error": True, "message": str(e)}

    def delete_room(self, room_id: str) -> dict:
        try:
            self.cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return {"success": True, "error": False, "message": "Комната удалена"}
            return {"success": False, "error": False, "message": "Комната не найдена"}
        except sqlite3.Error as e:
            return {"success": False, "error": True, "message": str(e)}

    def delete_user_rooms(self, user_id: int) -> dict:
        try:
            self.cursor.execute("DELETE FROM rooms WHERE creator_id = ?", (user_id,))
            self.connection.commit()
            return {"deleted_count": self.cursor.rowcount, "error": False}
        except sqlite3.Error as e:
            return {"deleted_count": 0, "error": True, "message": str(e)}


class SARoomsMixin:

    @staticmethod
    def _normalize_criteria(raw: list) -> list:
        return _normalize_criteria(raw)

    def create_room(self, creator_id: int, name: str, description: str = "",
                    language: str = "", criteria: list = None) -> dict:
        from ...models.orm import Room, generate_room_password

        session = self.get_session()
        try:
            new_room = Room(
                name=name,
                creator_id=creator_id,
                description=description,
                language=language,
                criteria=criteria or [],
                password=generate_room_password(),
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
        from ...models.orm import Room

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
                    "language": room.language or "",
                    "criteria": _normalize_criteria(room.criteria or []),
                    "created_at": room.created_at.isoformat() if room.created_at else None,
                    "participant_count": room.participant_count,
                    "password": room.password or "",
                },
                "error": False
            }
        finally:
            session.close()

    def get_user_rooms(self, user_id: int) -> dict:
        from ...models.orm import Room

        session = self.get_session()
        try:
            rooms = session.query(Room).filter(
                Room.creator_id == user_id
            ).order_by(Room.created_at.desc()).all()

            return {
                "rooms": [
                    {
                        "id": room.id,
                        "name": room.name,
                        "creator_id": room.creator_id,
                        "description": room.description,
                        "language": room.language or "",
                        "criteria": _normalize_criteria(room.criteria or []),
                        "created_at": room.created_at.isoformat() if room.created_at else None,
                        "participant_count": room.participant_count,
                        "password": room.password or "",
                    }
                    for room in rooms
                ],
                "error": False
            }
        except Exception as e:
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def get_all_user_rooms(self, user_id: int) -> dict:
        """Все комнаты пользователя: созданные им + те, в которые он вступил."""
        from ...models.orm import Room, RoomMember
        from sqlalchemy import or_

        session = self.get_session()
        try:
            rooms = (
                session.query(Room)
                .outerjoin(RoomMember, Room.id == RoomMember.room_id)
                .filter(or_(Room.creator_id == user_id, RoomMember.user_id == user_id))
                .distinct()
                .order_by(Room.created_at.desc())
                .all()
            )
            return {
                "rooms": [
                    {
                        "id": room.id,
                        "name": room.name,
                        "creator_id": room.creator_id,
                        "description": room.description,
                        "language": room.language or "",
                        "criteria": _normalize_criteria(room.criteria or []),
                        "created_at": room.created_at.isoformat() if room.created_at else None,
                        "participant_count": room.participant_count,
                        "password": room.password or "",
                    }
                    for room in rooms
                ],
                "error": False,
            }
        except Exception as e:
            return {"rooms": [], "error": True, "message": str(e)}
        finally:
            session.close()

    def delete_room(self, room_id: str) -> dict:
        from ...models.orm import Room

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

    def delete_user_rooms(self, user_id: int) -> dict:
        from ...models.orm import Room

        session = self.get_session()
        try:
            deleted_count = session.query(Room).filter(
                Room.creator_id == user_id
            ).delete(synchronize_session=False)
            session.commit()
            return {"deleted_count": deleted_count, "error": False}
        except Exception as e:
            session.rollback()
            return {"deleted_count": 0, "error": True, "message": str(e)}
        finally:
            session.close()
