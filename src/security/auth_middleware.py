"""
Middleware для аутентификации через JWT токены.
"""

from fastapi import Request, HTTPException, status
from typing import Callable
import jwt

from ..security.encryptors import decode_token


class JWTAuthMiddleware:
    """
    Middleware для проверки JWT токенов.

    Автоматически проверяет токены на защищенных эндпоинтах.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Args:
            secret_key: Секретный ключ для проверки подписи
            algorithm: Алгоритм шифрования
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def __call__(self, request: Request, call_next: Callable):
        """
        Обработка запроса.

        Args:
            request: Входящий запрос
            call_next: Следующий middleware в цепочке

        Returns:
            Response
        """
        # Список эндпоинтов без аутентификации
        public_paths = [
            "/health",
            "/sign_up",
            "/sign_in",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/info"
        ]

        # Пропускаем публичные эндпоинты
        if request.url.path in public_paths:
            return await call_next(request)

        # Для защищенных эндпоинтов проверяем токен
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Отсутствует токен авторизации",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Извлекаем токен из заголовка "Bearer <token>"
            scheme, token = auth_header.split()

            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверная схема авторизации. Используйте Bearer",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Декодируем и валидируем токен
            payload = decode_token(token, self.secret_key, self.algorithm)

            # Добавляем информацию о пользователе в request.state
            request.state.user_id = payload.get("user_id")
            request.state.email = payload.get("email")
            request.state.token = token

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен истек",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Невалидный токен: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Ошибка аутентификации: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Продолжаем обработку запроса
        response = await call_next(request)
        return response
