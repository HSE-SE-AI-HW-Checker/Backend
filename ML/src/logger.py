"""
Модуль логирования для LLaMA Local.
Предоставляет структурированное логирование с поддержкой различных уровней.
"""

import logging
import sys
from typing import Optional


class Logger:
    """Класс для структурированного логирования."""
    
    def __init__(self, name: str = "llama_local", level: str = "INFO"):
        """
        Инициализация логгера.
        
        Args:
            name: Имя логгера
            level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Удаляем существующие обработчики
        self.logger.handlers.clear()
        
        # Создаем обработчик для вывода в stderr
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, level.upper()))
        
        # Форматирование логов
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs):
        """Логирование отладочной информации."""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} {extra_info}".strip()
        self.logger.debug(full_message)
    
    def info(self, message: str, **kwargs):
        """Логирование информационных сообщений."""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} {extra_info}".strip()
        self.logger.info(full_message)
    
    def warning(self, message: str, **kwargs):
        """Логирование предупреждений."""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} {extra_info}".strip()
        self.logger.warning(full_message)
    
    def error(self, message: str, **kwargs):
        """Логирование ошибок."""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} {extra_info}".strip()
        self.logger.error(full_message)
    
    def critical(self, message: str, **kwargs):
        """Логирование критических ошибок."""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} {extra_info}".strip()
        self.logger.critical(full_message)
    
    def exception(self, message: str, exc_info: Optional[Exception] = None):
        """Логирование исключений с трассировкой."""
        self.logger.exception(message, exc_info=exc_info or True)