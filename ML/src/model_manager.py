"""
Модуль управления моделью LLaMA для LLaMA Local.
Обеспечивает загрузку модели и генерацию ответов с поддержкой streaming.
"""

from typing import Optional, Iterator, Dict, Any
from pathlib import Path


class ModelManager:
    """Класс для управления моделью LLaMA."""
    
    def __init__(self, config, logger=None):
        """
        Инициализация менеджера модели.
        
        Args:
            config: Конфигурация модели (ModelConfig)
            logger: Экземпляр логгера для записи событий
        """
        self.config = config
        self.logger = logger
        self.model = None
        self._is_loaded = False
    
    def load_model(self) -> None:
        """Загрузка модели LLaMA из файла."""
        try:
            # Проверяем существование файла модели
            model_path = Path(self.config.path)
            if not model_path.exists():
                raise FileNotFoundError(f"Файл модели не найден: {self.config.path}")
            
            if self.logger:
                self.logger.info(f"Загрузка модели из {self.config.path}")
                self.logger.info(f"Параметры: n_ctx={self.config.n_ctx}, n_gpu_layers={self.config.n_gpu_layers}")
            
            # Импортируем llama-cpp-python
            try:
                from llama_cpp import Llama
            except ImportError:
                raise ImportError(
                    "llama-cpp-python не установлен. "
                    "Установите с помощью: pip install llama-cpp-python"
                )
            
            # Загружаем модель с параметрами из конфигурации
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.config.n_ctx,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=False  # Отключаем verbose вывод llama.cpp
            )
            
            
            self._is_loaded = True
            
            if self.logger:
                self.logger.info("Модель успешно загружена")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка при загрузке модели: {e}")
            raise
    
    def generate_response(self, prompt: str) -> Iterator[str]:
        """
        Генерация ответа модели с поддержкой streaming.
        
        Args:
            prompt: Входной промпт для модели
            
        Yields:
            Токены ответа модели по мере их генерации
        """
        if not self._is_loaded or self.model is None:
            raise RuntimeError("Модель не загружена. Вызовите load_model() сначала.")
        
        try:
            if self.logger:
                self.logger.debug(f"Генерация ответа для промпта длиной {len(prompt)} символов")
            
            # Параметры генерации из конфигурации
            generation_params = {
                "prompt": prompt,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "repeat_penalty": self.config.repeat_penalty,
                "stream": self.config.stream,
                "stop": getattr(self.config, 'stop', [])
            }
            
            # Генерируем ответ
            if self.config.stream:
                # Streaming режим - возвращаем токены по мере генерации
                for output in self.model(**generation_params):
                    if "choices" in output and len(output["choices"]) > 0:
                        choice = output["choices"][0]
                        if "text" in choice:
                            yield choice["text"]
            else:
                # Не-streaming режим - возвращаем весь ответ сразу
                output = self.model(**generation_params)
                if "choices" in output and len(output["choices"]) > 0:
                    choice = output["choices"][0]
                    if "text" in choice:
                        yield choice["text"]
            
            if self.logger:
                self.logger.debug("Генерация ответа завершена")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка при генерации ответа: {e}")
            raise
    
    def generate_response_complete(self, prompt: str) -> str:
        """
        Генерация полного ответа модели без streaming.
        
        Args:
            prompt: Входной промпт для модели
            
        Returns:
            Полный ответ модели
        """
        response_parts = []
        for token in self.generate_response(prompt):
            response_parts.append(token)
        return ''.join(response_parts)
    
    def is_loaded(self) -> bool:
        """
        Проверка загружена ли модель.
        
        Returns:
            True если модель загружена, иначе False
        """
        return self._is_loaded
    
    def unload_model(self) -> None:
        """Выгрузка модели из памяти."""
        if self.model is not None:
            if self.logger:
                self.logger.info("Выгрузка модели")
            
            # Освобождаем ресурсы
            del self.model
            self.model = None
            self._is_loaded = False
            
            if self.logger:
                self.logger.info("Модель выгружена")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Получение информации о модели.
        
        Returns:
            Словарь с информацией о модели
        """
        return {
            "path": self.config.path,
            "loaded": self._is_loaded,
            "n_ctx": self.config.n_ctx,
            "n_gpu_layers": self.config.n_gpu_layers,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "repeat_penalty": self.config.repeat_penalty,
            "max_tokens": self.config.max_tokens,
            "stream": self.config.stream
        }