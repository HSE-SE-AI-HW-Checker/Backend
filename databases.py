import sqlite3
import hashlib
from safety.encryptors import sha256


class DB:
    def __init__(self):
        pass

    def execute(self, query):
        pass

    def add_user(self, username, email, password):
        pass

    def check_user(self, email, password):
        pass


class SQLite(DB):
    def __init__(self):
        self.connection = sqlite3.connect('AppUsers.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')

    def execute(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def add_user(self, username, email, password):
        if username is None:
            username = email.split('@')[0]

        password = sha256(password)
        try:
            self.execute(f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{password}')")
            return {"message": "Пользователь зарегистрирован"}
        except sqlite3.IntegrityError:
            return {"message": "Пользователь с таким email уже существует"}
        
    def check_user(self, email, password):
        password = sha256(password)
        self.execute(f"SELECT * FROM users WHERE email = '{email}'")
        if self.cursor.fetchone() is None:
            return {"message": f"Почта {email} не зарегистрирована"}
        

        self.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
        if self.cursor.fetchone() is None:
            return {"message": "Неверный пароль"}
        
        return {"message": ""}