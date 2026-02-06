import os
import sys
import importlib
import inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import discover_tests

TEST_RERUNS=10
TIME_BEETWEEN_RERUNS=2

def my_print(arg=''):
    VERBOSE = '-v' in sys.argv
    if VERBOSE:
        print(arg)

def run_all_tests():
    """
    Запуск всех тестов
    """
    tests = discover_tests(os.path.dirname(os.path.abspath(__file__)))

    if not tests:
        my_print("❌ Тесты не найдены!")
        return 0, 0
    
    passed = 0
    failed = 0
    errors = []
    
    my_print("=" * 70)
    my_print("ЗАПУСК ВСЕХ ТЕСТОВ")
    my_print("=" * 70)
    my_print(f"Найдено тестов: {len(tests)}")
    my_print("=" * 70)
    my_print()
    
    for test_name, test_func in tests:
        last_error = None
        for i in range(TEST_RERUNS):
            my_print(f"\n{'=' * 70}")
            my_print(f"Тест: {test_name}")
            my_print('=' * 70)

            try:
                test_func()
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
                break
            except Exception as e:
                last_error = e
        else:
                failed += 1
                error_msg = f"❌ {test_name} - ПРОВАЛЕН: {str(last_error)}"
                print(error_msg)
                errors.append(error_msg)
    
    # Итоговая статистика
    my_print("\n" + "=" * 70)
    my_print("ИТОГОВАЯ СТАТИСТИКА")
    my_print("=" * 70)
    my_print(f"Всего тестов: {len(tests)}")
    my_print(f"✅ Пройдено: {passed}")
    my_print(f"❌ Провалено: {failed}")
    print(f"Процент успеха: {(passed / len(tests) * 100):.1f}%")
    
    if errors:
        my_print("\n" + "=" * 70)
        my_print("ОШИБКИ:")
        my_print("=" * 70)
        for error in errors:
            my_print(error)
    
    my_print("\n" + "=" * 70)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    
    # Возвращаем код выхода: 0 если все тесты прошли, 1 если были ошибки
    sys.exit(0 if failed == 0 else 1)