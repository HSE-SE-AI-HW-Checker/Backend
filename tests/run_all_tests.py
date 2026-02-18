import os
import sys
import importlib
import inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import discover_tests

TEST_RERUNS=10
TIME_BEETWEEN_RERUNS=2

import logging

# Настройка логгера
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def run_all_tests():
    """
    Запуск всех тестов
    """
    tests = discover_tests(os.path.dirname(os.path.abspath(__file__)))

    if not tests:
        logger.error("❌ Тесты не найдены!")
        return 0, 0
    
    passed = 0
    failed = 0
    errors = []
    
    logger.info("=" * 70)
    logger.info("ЗАПУСК ВСЕХ ТЕСТОВ")
    logger.info("=" * 70)
    logger.info(f"Найдено тестов: {len(tests)}")
    logger.info("=" * 70)
    logger.info("")
    
    for test_name, test_func in tests:
        last_error = None
        for i in range(TEST_RERUNS):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"Тест: {test_name}")
            logger.info('=' * 70)

            try:
                test_func()
                passed += 1
                logger.info(f"✅ {test_name} - ПРОЙДЕН")
                break
            except Exception as e:
                last_error = e
        else:
                failed += 1
                error_msg = f"❌ {test_name} - ПРОВАЛЕН: {str(last_error)}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    # Итоговая статистика
    logger.info("\n" + "=" * 70)
    logger.info("ИТОГОВАЯ СТАТИСТИКА")
    logger.info("=" * 70)
    logger.info(f"Всего тестов: {len(tests)}")
    logger.info(f"✅ Пройдено: {passed}")
    logger.info(f"❌ Провалено: {failed}")
    logger.info(f"Процент успеха: {(passed / len(tests) * 100):.1f}%")

    if failed == 0:
        print("\033[32m" + 'Ok' + "\033[0m")
    
    if errors:
        logger.info("\n" + "=" * 70)
        logger.info("ОШИБКИ:")
        logger.info("=" * 70)
        for error in errors:
            logger.error(error)
    
    logger.info("\n" + "=" * 70)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    
    # Возвращаем код выхода: 0 если все тесты прошли, 1 если были ошибки
    sys.exit(0 if failed == 0 else 1)