"""
Модуль управления конфигурацией для LLaMA Local.
Загружает и валидирует параметры из YAML файла.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DownloadConfig:
    """Конфигурация загрузки модели."""
    repo_id: str
    filename: str
    auto_download: bool
    token: Optional[str] = None


@dataclass
class ModelConfig:
    """Конфигурация модели."""
    path: str
    n_ctx: int
    n_gpu_layers: int
    temperature: float
    top_p: float
    top_k: int
    repeat_penalty: float
    max_tokens: int
    stream: bool


@dataclass
class AppConfig:
    """Конфигурация приложения."""
    log_level: str


class ConfigManager:
    """Класс для управления конфигурацией приложения."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Инициализация менеджера конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
        self._download_config: Optional[DownloadConfig] = None
        self._model_config: Optional[ModelConfig] = None
        self._app_config: Optional[AppConfig] = None
    
    def load(self) -> None:
        """Загрузка конфигурации из YAML файла."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        self._validate_config()
        self._parse_config()
    
    def _validate_config(self) -> None:
        """Валидация структуры конфигурации."""
        if not self._config:
            raise ValueError("Конфигурация пуста")
        
        if 'download' not in self._config:
            raise ValueError("Отсутствует секция 'download' в конфигурации")
        
        if 'model' not in self._config:
            raise ValueError("Отсутствует секция 'model' в конфигурации")
        
        if 'app' not in self._config:
            raise ValueError("Отсутствует секция 'app' в конфигурации")
        
        # Проверка обязательных полей загрузки
        required_download_fields = ['repo_id', 'filename', 'auto_download']
        for field in required_download_fields:
            if field not in self._config['download']:
                raise ValueError(f"Отсутствует обязательное поле 'download.{field}'")
        
        # Проверка обязательных полей модели
        required_model_fields = ['path', 'n_ctx', 'n_gpu_layers']
        for field in required_model_fields:
            if field not in self._config['model']:
                raise ValueError(f"Отсутствует обязательное поле 'model.{field}'")
    
    def _parse_config(self) -> None:
        """Парсинг конфигурации в dataclass объекты."""
        # Парсим конфигурацию загрузки
        download_cfg = self._config['download']
        self._download_config = DownloadConfig(
            repo_id=download_cfg['repo_id'],
            filename=download_cfg['filename'],
            auto_download=download_cfg.get('auto_download', True),
            token=download_cfg.get('token')
        )
        
        model_cfg = self._config['model']
        self._model_config = ModelConfig(
            path=model_cfg['path'],
            n_ctx=model_cfg.get('n_ctx', 2048),
            n_gpu_layers=model_cfg.get('n_gpu_layers', -1),
            temperature=model_cfg.get('temperature', 0.7),
            top_p=model_cfg.get('top_p', 0.9),
            top_k=model_cfg.get('top_k', 40),
            repeat_penalty=model_cfg.get('repeat_penalty', 1.1),
            max_tokens=model_cfg.get('max_tokens', 512),
            stream=model_cfg.get('stream', True)
        )
        
        app_cfg = self._config['app']
        self._app_config = AppConfig(
            log_level=app_cfg.get('log_level', 'INFO')
        )
    
    @property
    def download(self) -> DownloadConfig:
        """Получение конфигурации загрузки."""
        if not self._download_config:
            raise RuntimeError("Конфигурация не загружена. Вызовите load() сначала.")
        return self._download_config
    
    @property
    def model(self) -> ModelConfig:
        """Получение конфигурации модели."""
        if not self._model_config:
            raise RuntimeError("Конфигурация не загружена. Вызовите load() сначала.")
        return self._model_config
    
    @property
    def app(self) -> AppConfig:
        """Получение конфигурации приложения."""
        if not self._app_config:
            raise RuntimeError("Конфигурация не загружена. Вызовите load() сначала.")
        return self._app_config
    
    def get_raw_config(self) -> Dict[str, Any]:
        """Получение сырой конфигурации."""
        if not self._config:
            raise RuntimeError("Конфигурация не загружена. Вызовите load() сначала.")
        return self._config