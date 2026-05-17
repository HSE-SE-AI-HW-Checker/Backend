import sqlite3


def _sqlite_row_to_member(row) -> dict:
    return {
        "user_id": row[0],
        "room_id": row[1],
        "ai_score": row[2],
        "final_score": row[3],
        "owner_score": row[4],
        "last_visit": str(row[5]),
        "submissions_count": row[6],
        "deadline": str(row[7]) if row[7] is not None else None,
        "submission_url": row[8] if len(row) > 8 else None,
        "owner_comment": row[9] if len(row) > 9 else None,
    }


class SQLiteRoomMembersMixin:

    def join_room(self, user_id: int, room_id: str) -> dict:
        try:
            self.cursor.execute(
                "INSERT INTO room_members (user_id, room_id) VALUES (?, ?)",
                (user_id, room_id),
            )
            self.connection.commit()
            return {"error": False}
        except sqlite3.IntegrityError as e:
            msg = str(e)
            if "UNIQUE" in msg or "PRIMARY KEY" in msg:
                return {"error": True, "message": "Пользователь уже является участником комнаты"}
            return {"error": True, "message": msg}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_room_member(self, user_id: int, room_id: str) -> dict:
        try:
            self.cursor.execute(
                "SELECT user_id, room_id, ai_score, final_score, owner_score, last_visit, submissions_count, deadline, submission_url, owner_comment "
                "FROM room_members WHERE user_id = ? AND room_id = ?",
                (user_id, room_id),
            )
            row = self.cursor.fetchone()
            if row is None:
                return {"member": None, "error": False}
            return {"member": _sqlite_row_to_member(row), "error": False}
        except sqlite3.Error as e:
            return {"member": None, "error": True, "message": str(e)}

    def get_room_members(self, room_id: str) -> dict:
        try:
            self.cursor.execute(
                "SELECT user_id, room_id, ai_score, final_score, owner_score, last_visit, submissions_count, deadline, submission_url, owner_comment "
                "FROM room_members WHERE room_id = ?",
                (room_id,),
            )
            rows = self.cursor.fetchall()
            return {"members": [_sqlite_row_to_member(r) for r in rows], "error": False}
        except sqlite3.Error as e:
            return {"members": [], "error": True, "message": str(e)}

    def get_room_members_with_users(self, room_id: str) -> dict:
        try:
            self.cursor.execute(
                """
                SELECT rm.user_id, rm.room_id, rm.ai_score, rm.final_score, rm.owner_score,
                       rm.last_visit, rm.submissions_count, rm.deadline, rm.submission_url,
                       rm.owner_comment, u.username, u.email
                FROM room_members rm
                JOIN users u ON rm.user_id = u.id
                WHERE rm.room_id = ?
                """,
                (room_id,),
            )
            rows = self.cursor.fetchall()
            members = []
            for row in rows:
                m = _sqlite_row_to_member(row)
                m["username"] = row[10]
                m["email"] = row[11]
                members.append(m)
            return {"members": members, "error": False}
        except sqlite3.Error as e:
            return {"members": [], "error": True, "message": str(e)}

    def update_owner_score(self, user_id: int, room_id: str, owner_score: float, owner_comment: str = None) -> dict:
        try:
            self.cursor.execute(
                "SELECT ai_score FROM room_members WHERE user_id = ? AND room_id = ?",
                (user_id, room_id),
            )
            row = self.cursor.fetchone()
            if row is None:
                return {"error": True, "message": "Участник комнаты не найден"}

            ai_score = row[0]
            updates = {"owner_score": owner_score}
            if ai_score is not None:
                updates["final_score"] = round(ai_score * 0.4 + owner_score * 0.6, 2)
            if owner_comment is not None:
                updates["owner_comment"] = owner_comment

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [user_id, room_id]
            self.cursor.execute(
                f"UPDATE room_members SET {set_clause} WHERE user_id = ? AND room_id = ?",
                values,
            )
            self.connection.commit()
            if self.cursor.rowcount == 0:
                return {"error": True, "message": "Участник комнаты не найден"}
            return {"error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def get_user_recent_rooms(self, user_id: int) -> dict:
        try:
            self.cursor.execute(
                """
                SELECT r.id, r.name, rm.last_visit, rm.submissions_count, r.participant_count, rm.final_score
                FROM room_members rm
                JOIN rooms r ON rm.room_id = r.id
                WHERE rm.user_id = ?
                ORDER BY rm.last_visit DESC
                """,
                (user_id,),
            )
            rows = self.cursor.fetchall()
            return {
                "rooms": [
                    {
                        "room_id": row[0],
                        "room_name": row[1],
                        "last_visit": str(row[2]),
                        "submissions_count": row[3],
                        "participant_count": row[4],
                        "final_score": row[5],
                    }
                    for row in rows
                ],
                "error": False,
            }
        except sqlite3.Error as e:
            return {"rooms": [], "error": True, "message": str(e)}

    def update_member_scores(self, user_id: int, room_id: str, **scores) -> dict:
        fields = {k: v for k, v in scores.items() if v is not None}
        if not fields:
            return {"error": True, "message": "Нет полей для обновления"}
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id, room_id]
        try:
            self.cursor.execute(
                f"UPDATE room_members SET {set_clause} WHERE user_id = ? AND room_id = ?",
                values,
            )
            self.connection.commit()
            if self.cursor.rowcount == 0:
                return {"error": True, "message": "Участник комнаты не найден"}
            return {"error": False}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}


class SARoomMembersMixin:

    def join_room(self, user_id: int, room_id: str) -> dict:
        from ...models.orm import RoomMember
        from sqlalchemy.exc import IntegrityError

        session = self.get_session()
        try:
            session.add(RoomMember(user_id=user_id, room_id=room_id))
            session.commit()
            return {"error": False}
        except IntegrityError:
            session.rollback()
            return {"error": True, "message": "Пользователь уже является участником комнаты"}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def get_room_member(self, user_id: int, room_id: str) -> dict:
        from ...models.orm import RoomMember

        session = self.get_session()
        try:
            member = session.query(RoomMember).filter(
                RoomMember.user_id == user_id,
                RoomMember.room_id == room_id,
            ).first()
            if member is None:
                return {"member": None, "error": False}
            return {"member": _sa_member_to_dict(member), "error": False}
        except Exception as e:
            return {"member": None, "error": True, "message": str(e)}
        finally:
            session.close()

    def get_room_members(self, room_id: str) -> dict:
        from ...models.orm import RoomMember

        session = self.get_session()
        try:
            members = session.query(RoomMember).filter(RoomMember.room_id == room_id).all()
            return {"members": [_sa_member_to_dict(m) for m in members], "error": False}
        except Exception as e:
            return {"members": [], "error": True, "message": str(e)}
        finally:
            session.close()

    def get_room_members_with_users(self, room_id: str) -> dict:
        from ...models.orm import RoomMember, User

        session = self.get_session()
        try:
            rows = (
                session.query(RoomMember, User.username, User.email)
                .join(User, RoomMember.user_id == User.id)
                .filter(RoomMember.room_id == room_id)
                .all()
            )
            members = []
            for member, username, email in rows:
                m = _sa_member_to_dict(member)
                m["username"] = username
                m["email"] = email
                members.append(m)
            return {"members": members, "error": False}
        except Exception as e:
            return {"members": [], "error": True, "message": str(e)}
        finally:
            session.close()

    def update_owner_score(self, user_id: int, room_id: str, owner_score: float, owner_comment: str = None) -> dict:
        from ...models.orm import RoomMember

        session = self.get_session()
        try:
            member = session.query(RoomMember).filter(
                RoomMember.user_id == user_id,
                RoomMember.room_id == room_id,
            ).first()
            if member is None:
                return {"error": True, "message": "Участник комнаты не найден"}

            updates = {"owner_score": owner_score}
            if member.ai_score is not None:
                updates["final_score"] = round(member.ai_score * 0.4 + owner_score * 0.6, 2)
            if owner_comment is not None:
                updates["owner_comment"] = owner_comment

            session.query(RoomMember).filter(
                RoomMember.user_id == user_id,
                RoomMember.room_id == room_id,
            ).update(updates)
            session.commit()
            return {"error": False}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def get_user_recent_rooms(self, user_id: int) -> dict:
        from ...models.orm import RoomMember, Room

        session = self.get_session()
        try:
            rows = (
                session.query(
                    Room.id,
                    Room.name,
                    RoomMember.last_visit,
                    RoomMember.submissions_count,
                    Room.participant_count,
                    RoomMember.final_score,
                )
                .join(Room, RoomMember.room_id == Room.id)
                .filter(RoomMember.user_id == user_id)
                .order_by(RoomMember.last_visit.desc())
                .all()
            )
            return {
                "rooms": [
                    {
                        "room_id": row[0],
                        "room_name": row[1],
                        "last_visit": row[2].isoformat() if row[2] else str(row[2]),
                        "submissions_count": row[3],
                        "participant_count": row[4],
                        "final_score": row[5],
                    }
                    for row in rows
                ],
                "error": False,
            }
        except Exception as e:
            return {"rooms": [], "error": True, "message": str(e)}
        finally:
            session.close()

    def update_member_scores(self, user_id: int, room_id: str, **scores) -> dict:
        from ...models.orm import RoomMember
        from datetime import datetime

        fields = {k: v for k, v in scores.items() if v is not None}
        if not fields:
            return {"error": True, "message": "Нет полей для обновления"}

        if "deadline" in fields and isinstance(fields["deadline"], str):
            fields["deadline"] = datetime.fromisoformat(fields["deadline"])
        if "last_visit" in fields and isinstance(fields["last_visit"], str):
            fields["last_visit"] = datetime.fromisoformat(fields["last_visit"])

        session = self.get_session()
        try:
            updated = session.query(RoomMember).filter(
                RoomMember.user_id == user_id,
                RoomMember.room_id == room_id,
            ).update(fields)
            session.commit()
            if updated == 0:
                return {"error": True, "message": "Участник комнаты не найден"}
            return {"error": False}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()


def _sa_member_to_dict(member) -> dict:
    return {
        "user_id": member.user_id,
        "room_id": member.room_id,
        "ai_score": member.ai_score,
        "final_score": member.final_score,
        "owner_score": member.owner_score,
        "last_visit": str(member.last_visit),
        "submissions_count": member.submissions_count,
        "deadline": member.deadline.isoformat() if member.deadline else None,
        "submission_url": member.submission_url,
        "owner_comment": member.owner_comment,
    }
