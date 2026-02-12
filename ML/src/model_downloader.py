"""
Модуль для автоматической загрузки моделей с Hugging Face.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError


class ModelDownloader:
    """Класс для автоматической загрузки моделей с Hugging Face."""
    
    def __init__(self, models_dir: str = "./models", logger=None):
        """
        Инициализация загрузчика моделей.
        
        Args:
            models_dir: Директория для сохранения моделей
            logger: Экземпляр логгера для записи событий
        """
        self.models_dir = Path(models_dir)
        self.logger = logger
        
        # Создаем директорию для моделей, если её нет
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def check_model_exists(self, filename: str) -> bool:
        """
        Проверка наличия модели в локальной директории.
        
        Args:
            filename: Имя файла модели
            
        Returns:
            True если модель существует, иначе False
        """
        model_path = self.models_dir / filename
        exists = model_path.exists() and model_path.is_file()
        
        if self.logger:
            if exists:
                self.logger.info(f"Модель найдена: {model_path}")
            else:
                self.logger.info(f"Модель не найдена: {model_path}")
        
        return exists
    
    def get_model_path(self, filename: str) -> Path:
        """
        Получение полного пути к файлу модели.
        
        Args:
            filename: Имя файла модели
            
        Returns:
            Полный путь к файлу модели
        """
        return self.models_dir / filename
    
    def check_disk_space(self, required_gb: float = 5.0) -> bool:
        """
        Проверка доступного места на диске.
        
        Args:
            required_gb: Требуемое место в ГБ
            
        Returns:
            True если достаточно места, иначе False
        """
        try:
            stat = shutil.disk_usage(self.models_dir)
            available_gb = stat.free / (1024 ** 3)
            
            if self.logger:
                self.logger.info(f"Доступно места на диске: {available_gb:.2f} ГБ")
            
            if available_gb < required_gb:
                if self.logger:
                    self.logger.warning(
                        f"Недостаточно места на диске. "
                        f"Требуется: {required_gb:.2f} ГБ, доступно: {available_gb:.2f} ГБ"
                    )
                return False
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка при проверке места на диске: {e}")
            return True  # Продолжаем, если не можем проверить
    
    def download_model(
        self,
        repo_id: str,
        filename: str,
        token: Optional[str] = None
    ) -> Path:
        """
        Загрузка модели с Hugging Face.
        
        Args:
            repo_id: ID репозитория на Hugging Face (например, "bartowski/Llama-3.2-1B-Instruct-GGUF")
            filename: Имя файла модели (например, "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
            token: Токен Hugging Face (опционально, для приватных моделей)
            
        Returns:
            Путь к загруженному файлу модели
            
        Raises:
            KeyboardInterrupt: Если загрузка прервана пользователем
            HfHubHTTPError: Если произошла ошибка при загрузке
            Exception: Другие ошибки
        """
        try:
            if self.logger:
                self.logger.info(f"Начало загрузки модели из {repo_id}/{filename}")
            
            print(f"\nЗагрузка модели с Hugging Face...")
            print(f"Репозиторий: {repo_id}")
            print(f"Файл: {filename}")
            print(f"Директория: {self.models_dir}")
            print("\nЭто может занять некоторое время в зависимости от размера модели и скорости интернета.")
            print("Нажмите Ctrl+C для отмены загрузки.\n")
            
            # Проверяем доступное место на диске
            if not self.check_disk_space():
                raise RuntimeError(
                    "Недостаточно места на диске для загрузки модели. "
                    "Освободите минимум 5 ГБ и попробуйте снова."
                )
            
            # Загружаем модель с Hugging Face
            # huggingface_hub автоматически показывает прогресс с помощью tqdm
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.models_dir),
                local_dir_use_symlinks=False,  # Копируем файл, а не создаем симлинк
                token=token,
                resume_download=True  # Поддержка возобновления загрузки
            )
            
            if self.logger:
                self.logger.info(f"Модель успешно загружена: {downloaded_path}")
            
            print(f"\n✓ Модель успешно загружена: {downloaded_path}\n")
            
            return Path(downloaded_path)
            
        except KeyboardInterrupt:
            if self.logger:
                self.logger.warning("Загрузка модели прервана пользователем")
            print("\n\n✗ Загрузка прервана пользователем")
            raise
            
        except HfHubHTTPError as e:
            error_msg = f"Ошибка HTTP при загрузке модели: {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            if e.response.status_code == 401:
                print("\n✗ Ошибка авторизации. Проверьте токен Hugging Face.")
            elif e.response.status_code == 404:
                print(f"\n✗ Модель не найдена: {repo_id}/{filename}")
                print("Проверьте правильность repo_id и filename в config.yaml")
            else:
                print(f"\n✗ {error_msg}")
            
            raise
            
        except Exception as e:
            error_msg = f"Ошибка при загрузке модели: {e}"
            if self.logger:
                self.logger.error(error_msg)
            print(f"\n✗ {error_msg}")
            raise
    
    def ensure_model_available(
        self,
        repo_id: str,
        filename: str,
        auto_download: bool = True,
        token: Optional[str] = None
    ) -> Path:
        """
        Проверка наличия модели и автоматическая загрузка при необходимости.
        
        Args:
            repo_id: ID репозитория на Hugging Face
            filename: Имя файла модели
            auto_download: Автоматически загружать модель, если она отсутствует
            token: Токен Hugging Face (опционально)
            
        Returns:
            Путь к файлу модели
            
        Raises:
            FileNotFoundError: Если модель не найдена и auto_download=False
            Exception: Другие ошибки при загрузке
        """
        model_path = self.get_model_path(filename)
        
        # Проверяем наличие модели
        if self.check_model_exists(filename):
            if self.logger:
                self.logger.info(f"Модель уже существует: {model_path}")
            return model_path
        
        # Модель не найдена
        if not auto_download:
            error_msg = (
                f"Модель не найдена: {model_path}\n"
                f"Установите auto_download: true в config.yaml для автоматической загрузки "
                f"или загрузите модель вручную."
            )
            if self.logger:
                self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Автоматическая загрузка
        if self.logger:
            self.logger.info("Модель не найдена, начинаем автоматическую загрузку")
        
        return self.download_model(repo_id, filename, token)