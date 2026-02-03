import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем все тестовые функции
from test_health_check import test_health_endpoint, test_info_endpoint
from test_sign_up import test_sign_up
from test_sign_in import test_sign_in_success, test_sign_in_wrong_password, test_sign_in_nonexistent_user
from test_log import test_log_endpoint, test_log_endpoint_empty_message, test_log_endpoint_long_message
from test_submit import (
    test_submit_git_link,
    test_submit_archive,
    test_submit_file_format,
    test_submit_unknown_type,
    test_submit_empty_data
)


def run_all_tests():
    """
    Запуск всех тестов
    """
    tests = [
        ("Health Check", test_health_endpoint),
        ("Info Endpoint", test_info_endpoint),
        ("Sign Up", test_sign_up),
        ("Sign In - Success", test_sign_in_success),
        ("Sign In - Wrong Password", test_sign_in_wrong_password),
        ("Sign In - Nonexistent User", test_sign_in_nonexistent_user),
        ("Log Endpoint", test_log_endpoint),
        ("Log - Empty Message", test_log_endpoint_empty_message),
        ("Log - Long Message", test_log_endpoint_long_message),
        ("Submit - Git Link", test_submit_git_link),
        ("Submit - Archive", test_submit_archive),
        ("Submit - File Format", test_submit_file_format),
        ("Submit - Unknown Type", test_submit_unknown_type),
        ("Submit - Empty Data", test_submit_empty_data),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    print("=" * 70)
    print("ЗАПУСК ВСЕХ ТЕСТОВ")
    print("=" * 70)
    print()
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 70}")
        print(f"Тест: {test_name}")
        print('=' * 70)
        
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name} - ПРОЙДЕН")
        except Exception as e:
            failed += 1
            error_msg = f"❌ {test_name} - ПРОВАЛЕН: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    # Итоговая статистика
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f"Всего тестов: {len(tests)}")
    print(f"✅ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    print(f"Процент успеха: {(passed / len(tests) * 100):.1f}%")
    
    if errors:
        print("\n" + "=" * 70)
        print("ОШИБКИ:")
        print("=" * 70)
        for error in errors:
            print(error)
    
    print("\n" + "=" * 70)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    
    # Возвращаем код выхода: 0 если все тесты прошли, 1 если были ошибки
    sys.exit(0 if failed == 0 else 1)