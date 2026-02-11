"""
Логгеры для Backend проекта.
"""

from .helpers import BackendPath


class Logger:
    """Базовый класс логгера."""
    
    def __init__(self, relative_file_path):
        """
        Args:
            relative_file_path: Путь к файлу логов относительно корня Backend
        """
        if relative_file_path:
            self.file_path = BackendPath(f'{relative_file_path}')
        else:
            self.file_path = None

    def log(self, message):
        """
        Записать сообщение в лог.
        
        Args:
            message: Сообщение для записи
        """
        raise NotImplementedError()


class SimpleLogger(Logger):
    """Простой логгер, выводящий в консоль и файл."""
    
    def __init__(self, relative_file_path=None):
        """
        Args:
            relative_file_path: Путь к файлу логов относительно корня Backend
        """
        super().__init__(relative_file_path)

    def log(self, message):
        """
        Записать сообщение в консоль и файл.
        
        Args:
            message: Сообщение для записи
        """
        print(message)
        if self.file_path:
            with open(self.file_path, 'a') as f:
                f.write(message + '\n')


class TestingLogger(Logger):
    """Логгер для тестирования."""
    
    def __init__(self, relative_file_path='tests/output/log.txt'):
        """
        Args:
            relative_file_path: Путь к файлу логов относительно корня Backend
        """
        super().__init__(relative_file_path)
        # Очищаем файл при инициализации
        with open(self.file_path, 'w') as f:
            f.write('')

    def log(self, message):
        """
        Записать сообщение в файл.
        
        Args:
            message: Сообщение для записи
        """
        with open(self.file_path, 'a') as f:
            f.write(message + '\n')


class OtherLogger(Logger):
    """Заглушка для других типов логгеров."""
    pass