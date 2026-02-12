"""
Модуль обработки сигналов для LLaMA Local.
Обеспечивает graceful shutdown при получении сигналов прерывания.
"""

import signal
import sys
from typing import Callable, Optional


class SignalHandler:
    """Класс для обработки системных сигналов."""
    
    def __init__(self, logger=None):
        """
        Инициализация обработчика сигналов.
        
        Args:
            logger: Экземпляр логгера для записи событий
        """
        self.logger = logger
        self.shutdown_requested = False
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
        self._cleanup_callback: Optional[Callable] = None
    
    def setup(self, cleanup_callback: Optional[Callable] = None) -> None:
        """
        Настройка обработчиков сигналов.
        
        Args:
            cleanup_callback: Функция для вызова при завершении работы
        """
        self._cleanup_callback = cleanup_callback
        
        # Сохраняем оригинальные обработчики
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_signal)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_signal)
        
        if self.logger:
            self.logger.debug("Обработчики сигналов настроены")
    
    def _handle_signal(self, signum: int, frame) -> None:
        """
        Обработка полученного сигнала.
        
        Args:
            signum: Номер сигнала
            frame: Текущий фрейм стека
        """
        signal_name = signal.Signals(signum).name
        
        if self.logger:
            self.logger.info(f"Получен сигнал {signal_name}, инициируется graceful shutdown")
        else:
            print(f"\nПолучен сигнал {signal_name}, завершение работы...", file=sys.stderr)
        
        self.shutdown_requested = True
        
        # Вызываем callback для очистки ресурсов
        if self._cleanup_callback:
            try:
                self._cleanup_callback()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Ошибка при выполнении cleanup callback: {e}")
                else:
                    print(f"Ошибка при очистке: {e}", file=sys.stderr)
        
        # Восстанавливаем оригинальные обработчики
        self.restore()
        
        # Завершаем процесс
        print("\nДо свидания!")
        sys.exit(0)
    
    def restore(self) -> None:
        """Восстановление оригинальных обработчиков сигналов."""
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
        
        if self.logger:
            self.logger.debug("Оригинальные обработчики сигналов восстановлены")
    
    def is_shutdown_requested(self) -> bool:
        """
        Проверка, был ли запрошен shutdown.
        
        Returns:
            True если shutdown был запрошен, иначе False
        """
        return self.shutdown_requested
    
    def request_shutdown(self) -> None:
        """Программный запрос на shutdown."""
        self.shutdown_requested = True
        if self.logger:
            self.logger.info("Программный запрос на shutdown")