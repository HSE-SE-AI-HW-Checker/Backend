import sqlite3


class SQLiteUsersMixin:

    def add_user(self, username, email, password):
        from ...security.encryptors import hash_password

        if username is None:
            username = email.split('@')[0]

        password_hash = hash_password(password)

        try:
            self.cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            self.connection.commit()
            return {
                "message": "Пользователь зарегистрирован",
                "error": False,
                "user_id": self.cursor.lastrowid
            }
        except sqlite3.IntegrityError:
            return {"message": "Пользователь с таким email уже существует", "error": True}

    def check_user(self, email, password):
        from ...security.encryptors import verify_password

        try:
            self.cursor.execute(
                "SELECT id, password FROM users WHERE email = ?",
                (email,)
            )
            result = self.cursor.fetchone()

            if result is None:
                return {"message": f"Почта {email} не зарегистрирована", "error": True}

            user_id, stored_password = result

            if not verify_password(password, stored_password):
                return {"message": "Неверный пароль", "error": True}

            return {"message": "", "error": False, "user_id": user_id}

        except sqlite3.Error as e:
            return {"message": str(e), "error": True}


class SAUsersMixin:

    def add_user(self, username, email, password):
        from ...security.encryptors import hash_password
        from ...models.orm import User
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
        from ...security.encryptors import verify_password
        from ...models.orm import User

        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()

            if user is None:
                return {"message": f"Почта {email} не зарегистрирована", "error": True}

            if not verify_password(password, user.password):
                return {"message": "Неверный пароль", "error": True}

            return {"message": "", "error": False, "user_id": user.id}
        finally:
            session.close()
