"""
Модуль обработки пользовательского ввода для LLaMA Local.
Читает промпты из stdin с поддержкой EOF и многострочного ввода.
"""

import sys
from typing import Optional


class InputHandler:
    """Класс для обработки пользовательского ввода."""
    
    def __init__(self, logger=None):
        """
        Инициализация обработчика ввода.
        
        Args:
            logger: Экземпляр логгера для записи событий
        """
        self.logger = logger
        self._eof_reached = False
    
    def read_prompt(self, prompt_text: str = "\nВведите промпт (Ctrl+D для завершения ввода, Ctrl+C для выхода):\n> ") -> Optional[str]:
        """
        Чтение промпта от пользователя.
        
        Args:
            prompt_text: Текст приглашения для ввода
            
        Returns:
            Введенный текст или None при EOF/ошибке
        """
        if self._eof_reached:
            return None
        
        try:
            # Выводим приглашение
            print(prompt_text, end='', flush=True)
            
            # Читаем строки до EOF (Ctrl+D)
            lines = []
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    # Ctrl+D нажат - завершаем ввод текущего промпта
                    break
            
            # Объединяем строки
            user_input = '\n'.join(lines).strip()
            
            if not user_input:
                if self.logger:
                    self.logger.debug("Получен пустой ввод")
                return None
            
            if self.logger:
                self.logger.debug(f"Получен промпт длиной {len(user_input)} символов")
            
            return user_input
            
        except KeyboardInterrupt:
            # Ctrl+C - пробрасываем исключение для обработки в main
            if self.logger:
                self.logger.debug("Получен KeyboardInterrupt при вводе")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка при чтении ввода: {e}")
            return None
    
    def read_multiline_prompt(self) -> Optional[str]:
        """
        Чтение многострочного промпта.
        Пользователь может вводить несколько строк, завершение по Ctrl+D.
        
        Returns:
            Введенный текст или None при EOF/ошибке
        """
        return self.read_prompt()
    
    def is_eof_reached(self) -> bool:
        """
        Проверка достижения EOF.
        
        Returns:
            True если EOF достигнут, иначе False
        """
        return self._eof_reached
    
    def reset_eof(self) -> None:
        """Сброс флага EOF."""
        self._eof_reached = False
    
    @staticmethod
    def print_response(text: str) -> None:
        """
        Вывод ответа модели.
        
        Args:
            text: Текст для вывода
        """
        print(text, end='', flush=True)
    
    @staticmethod
    def print_message(message: str) -> None:
        """
        Вывод информационного сообщения.
        
        Args:
            message: Сообщение для вывода
        """
        print(f"\n{message}", flush=True)