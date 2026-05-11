import sqlite3


class SQLiteLanguagesMixin:

    def get_all_languages(self) -> dict:
        try:
            self.cursor.execute("SELECT language FROM languages ORDER BY language")
            rows = self.cursor.fetchall()
            return {"languages": [row[0] for row in rows], "error": False}
        except sqlite3.Error as e:
            return {"languages": [], "error": True, "message": str(e)}

    def add_language(self, language: str) -> dict:
        try:
            self.cursor.execute("INSERT INTO languages (language) VALUES (?)", (language,))
            self.connection.commit()
            return {"error": False}
        except sqlite3.IntegrityError:
            return {"error": True, "message": f"Язык '{language}' уже существует"}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}

    def delete_language(self, language: str) -> dict:
        try:
            self.cursor.execute("DELETE FROM languages WHERE language = ?", (language,))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return {"error": False}
            return {"error": True, "message": f"Язык '{language}' не найден"}
        except sqlite3.Error as e:
            return {"error": True, "message": str(e)}


class SALanguagesMixin:

    def get_all_languages(self) -> dict:
        from ...models.orm import Language

        session = self.get_session()
        try:
            langs = session.query(Language).order_by(Language.language).all()
            return {"languages": [l.language for l in langs], "error": False}
        except Exception as e:
            return {"languages": [], "error": True, "message": str(e)}
        finally:
            session.close()

    def add_language(self, language: str) -> dict:
        from ...models.orm import Language
        from sqlalchemy.exc import IntegrityError

        session = self.get_session()
        try:
            session.add(Language(language=language))
            session.commit()
            return {"error": False}
        except IntegrityError:
            session.rollback()
            return {"error": True, "message": f"Язык '{language}' уже существует"}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()

    def delete_language(self, language: str) -> dict:
        from ...models.orm import Language

        session = self.get_session()
        try:
            deleted = session.query(Language).filter(Language.language == language).delete()
            session.commit()
            if deleted:
                return {"error": False}
            return {"error": True, "message": f"Язык '{language}' не найден"}
        except Exception as e:
            session.rollback()
            return {"error": True, "message": str(e)}
        finally:
            session.close()
