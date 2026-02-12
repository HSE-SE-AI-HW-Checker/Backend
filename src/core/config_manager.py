"""
Менеджер конфигурации для Backend проекта.
"""

import yaml
from pathlib import Path
from typing import Any
from ..models.config import ServerConfig
from ..utils.helpers import BackendPath, MLPath


def get_from_config(key: str, config: str = 'default') -> Any:
    """
    Получить значение из конфигурации по ключу.
    
    Args:
        key: Ключ параметра конфигурации
        config: Имя конфигурации (без расширения)
        
    Returns:
        Значение параметра конфигурации
    """
    config_obj = ServerConfig.from_config_name(config)
    return getattr(config_obj, key)


def get_url_from_config(config: str = 'default') -> str:
    """
    Получить URL сервера из конфигурации.
    
    Args:
        config: Имя конфигурации (без расширения)
        
    Returns:
        str: URL в формате http://host:port
    """
    return f'http://{get_from_config("host", config)}:{get_from_config("port", config)}'


def get_ml_server_address() -> str:
    """
    Получить адрес ML сервера из его конфигурации.
    
    Returns:
        str: URL ML сервера в формате http://host:port
    """
    config_path = MLPath('config.yaml')
    
    with open(str(config_path)) as f:
        config = yaml.safe_load(f)
    
    HOST = config.get('server', {}).get('host', '0.0.0.0')
    PORT = config.get('server', {}).get('port', 8000)

    return f'http://{HOST}:{PORT}'


def load_config(config_name: str = 'default') -> ServerConfig:
    """
    Загрузить конфигурацию по имени.
    
    Args:
        config_name: Имя конфигурации (без расширения)
        
    Returns:
        ServerConfig: Объект конфигурации
    """
    return ServerConfig.from_config_name(config_name)