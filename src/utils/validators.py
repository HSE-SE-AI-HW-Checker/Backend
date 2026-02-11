"""
Валидаторы данных для Backend проекта.
"""

import re
from typing import Optional
from .exceptions import ValidationError


def validate_email(email: str) -> bool:
    """
    Валидация email адреса.
    
    Args:
        email: Email адрес для проверки
        
    Returns:
        bool: True если email валиден
        
    Raises:
        ValidationError: Если email невалиден
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email должен быть непустой строкой")
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(f"Невалидный email адрес: {email}")
    
    return True


def validate_password(password: str, min_length: int = 6) -> bool:
    """
    Валидация пароля.
    
    Args:
        password: Пароль для проверки
        min_length: Минимальная длина пароля
        
    Returns:
        bool: True если пароль валиден
        
    Raises:
        ValidationError: Если пароль невалиден
    """
    if not password or not isinstance(password, str):
        raise ValidationError("Пароль должен быть непустой строкой")
    
    if len(password) < min_length:
        raise ValidationError(f"Пароль должен содержать минимум {min_length} символов")
    
    return True


def validate_username(username: Optional[str]) -> bool:
    """
    Валидация имени пользователя.
    
    Args:
        username: Имя пользователя для проверки
        
    Returns:
        bool: True если username валиден
        
    Raises:
        ValidationError: Если username невалиден
    """
    if username is None:
        return True
    
    if not isinstance(username, str):
        raise ValidationError("Username должен быть строкой")
    
    if len(username) < 3:
        raise ValidationError("Username должен содержать минимум 3 символа")
    
    if len(username) > 50:
        raise ValidationError("Username не должен превышать 50 символов")
    
    username_pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(username_pattern, username):
        raise ValidationError("Username может содержать только буквы, цифры, дефис и подчеркивание")
    
    return True


def validate_port(port: int) -> bool:
    """
    Валидация номера порта.
    
    Args:
        port: Номер порта
        
    Returns:
        bool: True если порт валиден
        
    Raises:
        ValidationError: Если порт невалиден
    """
    if not isinstance(port, int):
        raise ValidationError(f"Порт должен быть целым числом, получено: {type(port).__name__}")
    
    if not (1 <= port <= 65535):
        raise ValidationError(f"Порт должен быть в диапазоне 1-65535, получено: {port}")
    
    return True


def validate_host(host: str) -> bool:
    """
    Валидация хоста.
    
    Args:
        host: Хост для проверки
        
    Returns:
        bool: True если хост валиден
        
    Raises:
        ValidationError: Если хост невалиден
    """
    if not host or not isinstance(host, str):
        raise ValidationError("Host должен быть непустой строкой")
    
    return True