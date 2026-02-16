"""
Модели конфигурации для проекта.

Этот модуль содержит dataclass модели для работы с конфигурационными файлами.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class ServerConfig:
    """
    Конфигурация сервера приложения.

    Attributes:
        logger_implementation: Имя класса логгера (например, 'SimpleLogger', 'TestingLogger')
        log_file_path: Путь к файлу логов
        database_implementation: Имя класса реализации БД (например, 'SQLite')
        host: Хост сервера (например, 'localhost', '0.0.0.0')
        port: Порт сервера (1-65535)
        reload: Флаг автоматической перезагрузки при изменении кода
        drop_db: Флаг удаления базы данных при запуске
        jwt_secret_key: Секретный ключ для подписи JWT токенов (минимум 32 символа)
        jwt_algorithm: Алгоритм шифрования JWT (HS256, HS384, HS512)
        jwt_access_token_expire_minutes: Время жизни access token в минутах
        jwt_refresh_token_expire_days: Время жизни refresh token в днях
    """
    
    logger_implementation: str
    log_file_path: str
    database_implementation: str
    host: str
    port: int
    reload: bool
    drop_db: bool

    # JWT Authentication settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    def __post_init__(self):
        """Валидация полей после инициализации."""
        self._validate()
    
    def _validate(self):
        """
        Валидация значений конфигурации.
        
        Raises:
            ValueError: Если значения не соответствуют требованиям
        """
        # Валидация порта
        if not isinstance(self.port, int):
            raise ValueError(f"Порт должен быть целым числом, получено: {type(self.port).__name__}")
        
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Порт должен быть в диапазоне 1-65535, получено: {self.port}")
        
        # Валидация строковых полей
        if not self.logger_implementation or not isinstance(self.logger_implementation, str):
            raise ValueError("logger_implementation должен быть непустой строкой")
        
        if not self.log_file_path or not isinstance(self.log_file_path, str):
            raise ValueError("log_file_path должен быть непустой строкой")
        
        if not self.database_implementation or not isinstance(self.database_implementation, str):
            raise ValueError("database_implementation должен быть непустой строкой")
        
        if not self.host or not isinstance(self.host, str):
            raise ValueError("host должен быть непустой строкой")
        
        # Валидация булевых полей
        if not isinstance(self.reload, bool):
            raise ValueError(f"reload должен быть булевым значением, получено: {type(self.reload).__name__}")

        if not isinstance(self.drop_db, bool):
            raise ValueError(f"drop_db должен быть булевым значением, получено: {type(self.drop_db).__name__}")

        # Валидация JWT полей
        if not self.jwt_secret_key or not isinstance(self.jwt_secret_key, str):
            raise ValueError("jwt_secret_key должен быть непустой строкой")

        if len(self.jwt_secret_key) < 32:
            raise ValueError(f"jwt_secret_key должен быть не менее 32 символов для безопасности, получено: {len(self.jwt_secret_key)}")

        if self.jwt_algorithm not in ["HS256", "HS384", "HS512"]:
            raise ValueError(f"jwt_algorithm должен быть HS256, HS384 или HS512, получено: {self.jwt_algorithm}")

        if not isinstance(self.jwt_access_token_expire_minutes, int) or self.jwt_access_token_expire_minutes <= 0:
            raise ValueError("jwt_access_token_expire_minutes должен быть положительным целым числом")

        if not isinstance(self.jwt_refresh_token_expire_days, int) or self.jwt_refresh_token_expire_days <= 0:
            raise ValueError("jwt_refresh_token_expire_days должен быть положительным целым числом")
    
    @classmethod
    def from_yaml(cls, file_path: str) -> 'ServerConfig':
        """
        Загрузка конфигурации из YAML файла.
        
        Args:
            file_path: Путь к YAML файлу конфигурации
            
        Returns:
            ServerConfig: Объект конфигурации
            
        Raises:
            FileNotFoundError: Если файл не найден
            yaml.YAMLError: Если файл содержит невалидный YAML
            ValueError: Если конфигурация не соответствует требованиям
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not isinstance(config_data, dict):
            raise ValueError(f"Конфигурация должна быть словарем, получено: {type(config_data).__name__}")
        
        # Проверка наличия всех обязательных полей
        required_fields = {
            'logger_implementation', 'log_file_path', 'database_implementation',
            'host', 'port', 'reload', 'drop_db', 'jwt_secret_key'
        }
        missing_fields = required_fields - set(config_data.keys())
        
        if missing_fields:
            raise ValueError(f"Отсутствуют обязательные поля в конфигурации: {missing_fields}")
        
        return cls(**config_data)
    
    @classmethod
    def from_config_name(cls, config_name: str, configs_dir: str = "configs") -> 'ServerConfig':
        """
        Загрузка конфигурации по имени файла.
        
        Args:
            config_name: Имя конфигурации без расширения (например, 'default', 'testing')
            configs_dir: Директория с конфигурационными файлами (по умолчанию 'configs')
            
        Returns:
            ServerConfig: Объект конфигурации
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если конфигурация невалидна
            
        Examples:
            >>> config = ServerConfig.from_config_name('default')
            >>> config = ServerConfig.from_config_name('testing')
        """
        file_path = Path(configs_dir) / f"{config_name}.yaml"
        return cls.from_yaml(str(file_path))
    
    def to_dict(self) -> dict:
        """
        Преобразование конфигурации в словарь.

        Returns:
            dict: Словарь с параметрами конфигурации
        """
        return {
            'logger_implementation': self.logger_implementation,
            'log_file_path': self.log_file_path,
            'database_implementation': self.database_implementation,
            'host': self.host,
            'port': self.port,
            'reload': self.reload,
            'drop_db': self.drop_db,
            'jwt_secret_key': self.jwt_secret_key,
            'jwt_algorithm': self.jwt_algorithm,
            'jwt_access_token_expire_minutes': self.jwt_access_token_expire_minutes,
            'jwt_refresh_token_expire_days': self.jwt_refresh_token_expire_days
        }
    
    def __repr__(self) -> str:
        """Строковое представление конфигурации."""
        return (
            f"ServerConfig("
            f"logger={self.logger_implementation}, "
            f"db={self.database_implementation}, "
            f"host={self.host}:{self.port}, "
            f"reload={self.reload}, "
            f"drop_db={self.drop_db})"
        )