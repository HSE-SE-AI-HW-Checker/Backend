import sqlite3


class SQLiteSessionsMixin:

    def create_session(self, user_id: int, token: str, expires_at: str,
                       user_agent: str = None, ip_address: str = None) -> dict:
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

            from datetime import datetime
            expires = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expires:
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
        try:
            self.cursor.execute("""
                UPDATE sessions SET is_active = 0 WHERE token = ?
            """, (token,))
            self.connection.commit()

            if self.cursor.rowcount > 0:
                return {"success": True, "error": False, "message": "Токен успешно отозван"}
            else:
                return {"success": False, "error": False, "message": "Токен не найден"}

        except sqlite3.Error as e:
            return {"success": False, "error": True, "message": str(e)}


class SASessionsMixin:

    def create_session(self, user_id: int, token: str, expires_at: str,
                       user_agent: str = None, ip_address: str = None) -> dict:
        from ...models.orm import Session
        from datetime import datetime

        session = self.get_session()
        try:
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
        from ...models.orm import Session, User
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

            if datetime.utcnow() > db_session.expires_at:
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
        from ...models.orm import Session

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
