"""
Функции шифрования для Backend проекта.
"""

import hashlib


def sha256(data: str) -> str:
    """
    Хеширование данных с использованием SHA-256.
    
    Args:
        data: Данные для хеширования
        
    Returns:
        str: Хеш в шестнадцатеричном формате
    """
    return hashlib.sha256(data.encode()).hexdigest()


def bcrypt(data: str) -> str:
    """
    Хеширование данных с использованием bcrypt.
    
    Args:
        data: Данные для хеширования
        
    Returns:
        str: Хеш
        
    Note:
        Требует установки библиотеки bcrypt
    """
    # TODO: Реализовать bcrypt хеширование
    pass