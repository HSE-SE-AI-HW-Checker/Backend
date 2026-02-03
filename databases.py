import sqlite3
import hashlib
from safety.encryptors import sha256
import os

from util import get_main_directory

class DB:
    def __init__(self):
        raise NotImplementedError()

    def execute(self, query):
        raise NotImplementedError()

    def add_user(self, username, email, password):
        raise NotImplementedError()

    def check_user(self, email, password):
        raise NotImplementedError()

    def drop(self):
        raise NotImplementedError()


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
            return {"message": "Пользователь зарегистрирован", "error": False}
        except sqlite3.IntegrityError:
            return {"message": "Пользователь с таким email уже существует", "error": True}
        
    def check_user(self, email, password):
        password = sha256(password)
        self.execute(f"SELECT * FROM users WHERE email = '{email}'")
        if self.cursor.fetchone() is None:
            return {"message": f"Почта {email} не зарегистрирована", "error": True}
        

        self.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
        if self.cursor.fetchone() is None:
            return {"message": "Неверный пароль", "error": True}
        
        return {"message": "", "error": False}
    
    def drop():
        if os.path.exists(f'{get_main_directory()}/AppUsers.db'):
            os.remove(f'{get_main_directory()}/AppUsers.db')