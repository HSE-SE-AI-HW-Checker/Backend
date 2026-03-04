"""HTTP-клиент для вызова ML-сервиса (/generate non-stream)."""

from __future__ import annotations

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


def ml_generate_non_stream(
    ml_url: str,
    prompt: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    timeout: int = 120,
) -> str:
    """
    Вызывает POST /generate без streaming и возвращает текст ответа.
    При ошибках HTTP пробрасывает requests.HTTPError или RequestException.
    """
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    response = requests.post(
        f"{ml_url.rstrip('/')}/generate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    body = response.json()
    text = body.get("text", "")
    if not isinstance(text, str):
        logger.warning("ML /generate вернул не строку в поле text")
        return str(text)
    return text
