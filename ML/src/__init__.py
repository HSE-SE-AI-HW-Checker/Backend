"""
LLaMA Local - локальный запуск квантизированных моделей LLaMA на MacOS.

Модульная архитектура для работы с llama-cpp-python и Metal поддержкой.
"""

from .logger import Logger
from .config_manager import ConfigManager, ModelConfig, AppConfig, DownloadConfig
from .signal_handler import SignalHandler
from .input_handler import InputHandler
from .model_manager import ModelManager
from .model_downloader import ModelDownloader

__version__ = "1.0.0"
__all__ = [
    "Logger",
    "ConfigManager",
    "ModelConfig",
    "AppConfig",
    "DownloadConfig",
    "SignalHandler",
    "InputHandler",
    "ModelManager",
    "ModelDownloader",
]