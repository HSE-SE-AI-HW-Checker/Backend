#!/usr/bin/env python3
"""
LLaMA Local - главный модуль приложения.
Запуск локальной квантизированной модели LLaMA на MacOS с Metal поддержкой.
"""

import sys
from pathlib import Path

# Добавляем src в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    Logger,
    ConfigManager,
    SignalHandler,
    InputHandler,
    ModelManager,
    ModelDownloader,
)


class LLaMALocal:
    """Главный класс приложения LLaMA Local."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Инициализация приложения.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = config_path
        self.logger = None
        self.config_manager = None
        self.signal_handler = None
        self.input_handler = None
        self.model_manager = None
        self.running = False
    
    def initialize(self) -> bool:
        """
        Инициализация всех компонентов приложения.
        
        Returns:
            True если инициализация успешна, иначе False
        """
        try:
            # Загружаем конфигурацию
            print("Загрузка конфигурации...")
            self.config_manager = ConfigManager(self.config_path)
            self.config_manager.load()
            
            # Инициализируем логгер
            self.logger = Logger(
                name="llama_local",
                level=self.config_manager.app.log_level
            )
            self.logger.info("LLaMA Local запущен")
            self.logger.info(f"Конфигурация загружена из {self.config_path}")
            
            # Инициализируем обработчик сигналов
            self.signal_handler = SignalHandler(logger=self.logger)
            self.signal_handler.setup(cleanup_callback=self._cleanup)
            
            # Инициализируем обработчик ввода
            self.input_handler = InputHandler(logger=self.logger)
            
            # Инициализируем загрузчик моделей
            self.model_downloader = ModelDownloader(
                models_dir="./models",
                logger=self.logger
            )
            
            # Проверяем наличие модели и загружаем при необходимости
            download_config = self.config_manager.download
            try:
                model_path = self.model_downloader.ensure_model_available(
                    repo_id=download_config.repo_id,
                    filename=download_config.filename,
                    auto_download=download_config.auto_download,
                    token=download_config.token
                )
                self.logger.info(f"Модель доступна: {model_path}")
            except FileNotFoundError as e:
                print(f"\nОшибка: {e}", file=sys.stderr)
                self.logger.error(str(e))
                return False
            except KeyboardInterrupt:
                print("\n\nЗагрузка прервана пользователем")
                self.logger.warning("Загрузка модели прервана")
                return False
            except Exception as e:
                print(f"\nОшибка при загрузке модели: {e}", file=sys.stderr)
                self.logger.error(f"Ошибка при загрузке модели: {e}")
                return False
            
            # Инициализируем менеджер модели
            self.model_manager = ModelManager(
                config=self.config_manager.model,
                logger=self.logger
            )
            
            # Загружаем модель
            print("Загрузка модели LLaMA...")
            self.logger.info("Начало загрузки модели")
            self.model_manager.load_model()
            print("Модель успешно загружена!")
            
            # Выводим информацию о модели
            model_info = self.model_manager.get_model_info()
            self.logger.info(f"Модель: {model_info['path']}")
            self.logger.info(f"Контекст: {model_info['n_ctx']} токенов")
            self.logger.info(f"GPU слои: {model_info['n_gpu_layers']}")
            
            return True
            
        except FileNotFoundError as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            if self.logger:
                self.logger.error(str(e))
            return False
        except Exception as e:
            print(f"Ошибка при инициализации: {e}", file=sys.stderr)
            if self.logger:
                self.logger.exception("Ошибка при инициализации")
            return False
    
    def _cleanup(self) -> None:
        """Очистка ресурсов при завершении работы."""
        if self.logger:
            self.logger.info("Выполняется очистка ресурсов")
        
        if self.model_manager and self.model_manager.is_loaded():
            self.model_manager.unload_model()
    
    def run(self) -> int:
        """
        Основной цикл работы приложения.
        
        Returns:
            Код возврата (0 - успех, 1 - ошибка)
        """
        if not self.initialize():
            return 1
        
        self.running = True
        
        # Приветственное сообщение
        print("\n" + "="*70)
        print("LLaMA Local - локальный запуск квантизированных моделей LLaMA")
        print("="*70)
        print("\nИнструкции:")
        print("  - Введите промпт и нажмите Ctrl+D для отправки")
        print("  - Нажмите Ctrl+C для выхода из программы")
        print("="*70 + "\n")
        
        try:
            # Основной цикл обработки промптов
            while self.running and not self.signal_handler.is_shutdown_requested():
                try:
                    # Читаем промпт от пользователя
                    prompt = self.input_handler.read_prompt()
                    
                    if prompt is None:
                        # Пустой ввод или EOF - продолжаем
                        continue
                    
                    if self.signal_handler.is_shutdown_requested():
                        break
                    
                    # Логируем промпт
                    self.logger.info(f"Обработка промпта: {prompt[:50]}...")
                    
                    # Генерируем ответ
                    print("\nОтвет модели:")
                    print("-" * 70)
                    
                    try:
                        for token in self.model_manager.generate_response(prompt):
                            if self.signal_handler.is_shutdown_requested():
                                print("\n\n[Генерация прервана]")
                                break
                            self.input_handler.print_response(token)
                        
                        print("\n" + "-" * 70)
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка при генерации ответа: {e}")
                        print(f"\nОшибка при генерации ответа: {e}", file=sys.stderr)
                    
                    if self.signal_handler.is_shutdown_requested():
                        break
                
                except KeyboardInterrupt:
                    # Ctrl+C - выходим из цикла
                    self.logger.info("Получен сигнал прерывания")
                    break
                except EOFError:
                    # EOF в stdin - продолжаем работу
                    continue
                except Exception as e:
                    self.logger.error(f"Ошибка в основном цикле: {e}")
                    print(f"\nОшибка: {e}", file=sys.stderr)
            
            # Завершение работы (если вышли из цикла нормально, без сигнала)
            if not self.signal_handler.is_shutdown_requested():
                print("\n\nЗавершение работы...")
                self.logger.info("Завершение работы приложения")
                self._cleanup()
                
                if self.signal_handler:
                    self.signal_handler.restore()
                
                print("До свидания!")
            
            return 0
            
        except Exception as e:
            self.logger.exception("Критическая ошибка в основном цикле")
            print(f"\nКритическая ошибка: {e}", file=sys.stderr)
            return 1


def main() -> int:
    """
    Точка входа в приложение.
    
    Returns:
        Код возврата
    """
    # Проверяем аргументы командной строки
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Создаем и запускаем приложение
    app = LLaMALocal(config_path=config_path)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())