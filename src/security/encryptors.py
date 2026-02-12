"""
Функции шифрования для Backend проекта.
"""

import hashlib
import bcrypt as bcrypt_lib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt


# ============================================================================
# УСТАРЕВШАЯ ФУНКЦИЯ (для обратной совместимости)
# ============================================================================

def sha256(data: str) -> str:
    """
    Хеширование данных с использованием SHA-256.

    DEPRECATED: Используйте hash_password() для новых реализаций.
    Эта функция оставлена для обратной совместимости.

    Args:
        data: Данные для хеширования

    Returns:
        str: Хеш в шестнадцатеричном формате
    """
    return hashlib.sha256(data.encode()).hexdigest()


# ============================================================================
# BCRYPT - БЕЗОПАСНОЕ ХЕШИРОВАНИЕ ПАРОЛЕЙ
# ============================================================================

def hash_password(password: str) -> str:
    """
    Хеширование пароля с использованием bcrypt.

    Args:
        password: Пароль для хеширования

    Returns:
        str: Хеш пароля (включает соль)

    Note:
        Bcrypt автоматически генерирует соль и добавляет её к хешу.
        Хеш можно безопасно хранить в БД.

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> print(hashed)
        $2b$12$KIX...
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt_lib.gensalt()
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка соответствия пароля хешу.

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хеш из базы данных

    Returns:
        bool: True если пароль совпадает, False в противном случае

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt_lib.checkpw(password_bytes, hashed_bytes)


# ============================================================================
# JWT - УПРАВЛЕНИЕ ТОКЕНАМИ
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создать JWT access token.

    Args:
        data: Данные для включения в payload токена (обычно user_id, email)
        secret_key: Секретный ключ для подписи
        algorithm: Алгоритм шифрования (по умолчанию HS256)
        expires_delta: Время жизни токена (по умолчанию 30 минут)

    Returns:
        str: JWT токен

    Example:
        >>> token = create_access_token(
        ...     data={"user_id": 123, "email": "user@example.com"},
        ...     secret_key="secret"
        ... )
    """
    to_encode = data.copy()

    # Установка времени истечения
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)

    # Добавление стандартных claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # Создание токена
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

    return encoded_jwt


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256"
) -> Dict[str, Any]:
    """
    Декодировать и валидировать JWT токен.

    Args:
        token: JWT токен
        secret_key: Секретный ключ для проверки подписи
        algorithm: Алгоритм шифрования

    Returns:
        dict: Payload токена

    Raises:
        jwt.ExpiredSignatureError: Токен истек
        jwt.InvalidTokenError: Токен невалидный

    Example:
        >>> try:
        ...     payload = decode_token(token, secret_key)
        ...     user_id = payload['user_id']
        ... except jwt.ExpiredSignatureError:
        ...     print("Token expired")
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Токен истек")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Невалидный токен: {str(e)}")


def create_tokens_pair(
    user_id: int,
    email: str,
    secret_key: str,
    algorithm: str = "HS256",
    access_expire_minutes: int = 30,
    refresh_expire_days: int = 7
) -> Dict[str, str]:
    """
    Создать пару токенов: access и refresh.

    Args:
        user_id: ID пользователя
        email: Email пользователя
        secret_key: Секретный ключ
        algorithm: Алгоритм шифрования
        access_expire_minutes: Время жизни access token в минутах
        refresh_expire_days: Время жизни refresh token в днях

    Returns:
        dict: {'access_token': str, 'refresh_token': str, 'token_type': 'bearer'}

    Example:
        >>> tokens = create_tokens_pair(
        ...     user_id=123,
        ...     email="user@example.com",
        ...     secret_key="secret"
        ... )
        >>> print(tokens['access_token'])
    """
    # Payload для токенов
    token_data = {
        "user_id": user_id,
        "email": email
    }

    # Access token (короткий срок жизни)
    access_token = create_access_token(
        data=token_data,
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(minutes=access_expire_minutes)
    )

    # Refresh token (длинный срок жизни)
    refresh_data = token_data.copy()
    refresh_data["type"] = "refresh"

    refresh_token = create_access_token(
        data=refresh_data,
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(days=refresh_expire_days)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# Deprecated alias for backward compatibility
def bcrypt(data: str) -> str:
    """
    DEPRECATED: Используйте hash_password() вместо этой функции.

    Args:
        data: Данные для хеширования

    Returns:
        str: Хеш
    """
    return hash_password(data)