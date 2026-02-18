"""
Логгеры для Backend проекта.
"""

import logging
import sys
from pathlib import Path
from .helpers import BackendPath


class Logger:
    """Базовый класс логгера (адаптер для logging)."""
    
    def __init__(self, relative_file_path: str, mode: str = 'a', to_console: bool = True, log_level: str = 'WARNING'):
        """
        Args:
            relative_file_path: Путь к файлу логов относительно корня Backend
            mode: Режим открытия файла ('a' - append, 'w' - write/overwrite)
            to_console: Выводить ли логи в консоль
            log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger("backend_logger")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers = []  # Очищаем существующие хендлеры

        formatter = logging.Formatter('%(message)s')

        if relative_file_path:
            file_path = BackendPath(f'{relative_file_path}')
            # Создаем директорию, если она не существует
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(file_path, mode=mode, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        if to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log(self, message):
        """
        Записать сообщение в лог.
        
        Args:
            message: Сообщение для записи
        """
        self.logger.info(message)