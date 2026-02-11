"""
Кастомные исключения для Backend проекта.
"""


class BackendException(Exception):
    """Базовое исключение для всех ошибок Backend."""
    pass


class ConfigurationError(BackendException):
    """Ошибка конфигурации."""
    pass


class DatabaseError(BackendException):
    """Ошибка работы с базой данных."""
    pass


class ValidationError(BackendException):
    """Ошибка валидации данных."""
    pass


class AuthenticationError(BackendException):
    """Ошибка аутентификации."""
    pass


class ServerError(BackendException):
    """Ошибка сервера."""
    pass