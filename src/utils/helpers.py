"""
Вспомогательные функции для Backend проекта.
"""

import os
import sys
import importlib
from pathlib import Path
from src.services.github_service import GitHubRepoExplorer
from src.services.archive_service import ArchiveProcessor

class BackendPath:
    """
    Класс для работы с путями относительно корня Backend проекта.
    """
    
    def __init__(self, path_from_root=''):
        """
        Args:
            path_from_root: Путь к файлу относительно Backend/
        """
        self.path = os.path.join(BackendPath._get_root_path(), path_from_root)

    @staticmethod
    def _get_root_path():
        """Получить корневой путь Backend проекта."""
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def __str__(self):
        return str(self.path)
    
    def __repr__(self):
        return f"BackendPath('{self.path}')"
    
    def __fspath__(self):
        """Поддержка протокола os.PathLike для использования с open(), os.path и т.д."""
        return self.path
    
    def __truediv__(self, other):
        """Поддержка оператора / для создания путей."""
        return BackendPath(os.path.join(self.path, str(other)))
    
    def __add__(self, other):
        """Поддержка конкатенации со строками."""
        return str(self.path) + str(other)
    
    def __radd__(self, other):
        """Поддержка конкатенации со строками слева."""
        return str(other) + str(self.path)


class MLPath(BackendPath):
    """
    Класс для работы с путями относительно ML директории.
    """
    
    def __init__(self, path_from_root=''):
        self.path = BackendPath(f'ML/{path_from_root}')


def get_implementation(module_name: str, class_name: str):
    """
    Получить класс по имени модуля и класса.
    
    Args:
        module_name: Имя модуля
        class_name: Имя класса
        
    Returns:
        Класс из указанного модуля
    """
    return getattr(importlib.import_module(module_name), class_name)


def available_implementations(module_name: str, base_class_name: str = 'Logger'):
    """
    Получить список доступных реализаций базового класса.
    
    Args:
        module_name: Имя модуля
        base_class_name: Имя базового класса
        
    Returns:
        list: Список имен классов-наследников
    """
    ans = []
    base_class = getattr(importlib.import_module(module_name), base_class_name)
    for elem in base_class.__subclasses__():
        ans.append(elem.__name__)
    return ans


def parse_args(args: list) -> dict:
    """
    Парсинг аргументов командной строки.
    
    Args:
        args: Список аргументов
        
    Returns:
        dict: Словарь с распарсенными аргументами
    """
    ans = {}
    for arg in args:
        if '=' not in arg:
            ans[arg] = True
            continue
        key, value = arg.split('=', 1)
        ans[key] = value
    return ans


def parse_submitted_data(submitted_data):
    """
    Парсинг данных, отправленных на сервер.
    
    Args:
        submitted_data: Объект с отправленными на сервер данными
        
    Returns:
        Данные в формате, который может обработать ML (скорее всего base64 encoded)
    """
    # Ссылка на git подобную штуку
    if submitted_data.data_type == 0:
        explorer = GitHubRepoExplorer(token="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", whitelist=['.cpp', '.h', '.hpp', '.py', '.txt', '.java'])
        return explorer.get_repo_contents(submitted_data.data)
    # Архив 
    elif submitted_data.data_type == 1:
        processor = ArchiveProcessor(whitelist=['.cpp', '.h', '.hpp', '.py', '.txt'])
        return processor.process_base64_archive(submitted_data.data)
    # Формат с окошком на каждый файл (обсуждали в личке)
    elif submitted_data.data_type == 2:
        pass
    else:
        return None