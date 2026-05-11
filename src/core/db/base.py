class DB:
    """Базовый класс для работы с базой данных."""

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
