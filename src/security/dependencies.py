"""
FastAPI Dependencies для аутентификации.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging

logger = logging.getLogger(__name__)

from ..security.encryptors import decode_token
from ..core.database_manager import SQLite


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency для получения текущего пользователя из токена.

    Args:
        request: FastAPI Request объект
        credentials: Credentials из Bearer токена

    Returns:
        dict: Информация о пользователе {user_id, email, username}

    Raises:
        HTTPException: Если токен невалидный или истек

    Example:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    token = credentials.credentials

    logger.info(f"🔐 [BACKEND] Получен токен: {token[:20]}...")

    # Получаем конфигурацию из request (server instance)
    # Конфигурация будет доступна через server instance
    try:
        # Пытаемся получить server instance из app.state
        server = request.app.state.server
        config = server.config
        db = server.db
    except AttributeError:
        # Если не получилось, используем default значения
        from ..models.config import ServerConfig
        from ..core.database_manager import SQLite
        config = ServerConfig.from_config_name('default')
        db = SQLite()

    try:
        # Декодируем токен
        payload = decode_token(
            token,
            config.jwt_secret_key,
            config.jwt_algorithm
        )

        user_id = payload.get("user_id")
        email = payload.get("email")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный payload токена",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем токен в БД
        validation_result = db.validate_token(token)

        if not validation_result.get("valid", False):
            logging.error(f"❌ [BACKEND] Токен невалидный: {validation_result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=validation_result.get("message", "Токен невалидный"),
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"✅ [BACKEND] Токен валидный для user_id={user_id}, email={email}")
        return {
            "user_id": user_id,
            "email": email,
            "username": validation_result.get("username"),
            "session_id": validation_result.get("session_id")
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[dict]:
    """
    Как get_current_user, но без Bearer возвращает None;
    при невалидном токене также None (эндпоинт трактует запрос как анонимный).
    """
    if credentials is None:
        return None
    token = credentials.credentials
    try:
        server = request.app.state.server
        config = server.config
        db = server.db
    except AttributeError:
        return None

    try:
        payload = decode_token(
            token,
            config.jwt_secret_key,
            config.jwt_algorithm,
        )

        user_id = payload.get("user_id")
        email = payload.get("email")

        if user_id is None or email is None:
            return None

        validation_result = db.validate_token(token)

        if not validation_result.get("valid", False):
            return None

        return {
            "user_id": user_id,
            "email": email,
            "username": validation_result.get("username"),
            "session_id": validation_result.get("session_id"),
        }

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
        return None
