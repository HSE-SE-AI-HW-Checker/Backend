import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from src.core.config_manager import get_url_from_config
from tests.utils_for_tests import with_test_server, my_print

CONFIG = 'testing'

BASE_URL = get_url_from_config(CONFIG)
HEADERS = {'Content-Type': 'application/json'}


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_sign_in_success():
    """
    Тест успешной авторизации пользователя
    """
    # Сначала регистрируем пользователя
    sign_up_url = f'{BASE_URL}/sign_up'
    sign_up_data = {
        'username': 'TestUser',
        'email': 'testuser@example.com',
        'password': 'securepassword123'
    }
    
    sign_up_response = requests.post(sign_up_url, json=sign_up_data, headers=HEADERS)
    assert sign_up_response.status_code == 200, "Не удалось зарегистрировать пользователя"
    my_print("✓ Пользователь зарегистрирован")
    
    # Теперь пытаемся авторизоваться
    sign_in_url = f'{BASE_URL}/sign_in'
    sign_in_data = {
        'email': 'testuser@example.com',
        'password': 'securepassword123'
    }
    
    response = requests.get(sign_in_url, json=sign_in_data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert 'error' in response_data, "Отсутствует поле 'error' в ответе"
    assert response_data['error'] == False, "Ожидалось error=False для успешной авторизации"
    my_print("✓ Авторизация прошла успешно")
    
    my_print("\n✅ Тест успешной авторизации пройден!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_sign_in_wrong_password():
    """
    Тест авторизации с неверным паролем
    """
    # Сначала регистрируем пользователя
    sign_up_url = f'{BASE_URL}/sign_up'
    sign_up_data = {
        'username': 'TestUser2',
        'email': 'testuser2@example.com',
        'password': 'correctpassword'
    }
    
    sign_up_response = requests.post(sign_up_url, json=sign_up_data, headers=HEADERS)
    assert sign_up_response.status_code == 200, "Не удалось зарегистрировать пользователя"
    my_print("✓ Пользователь зарегистрирован")
    
    # Пытаемся авторизоваться с неверным паролем
    sign_in_url = f'{BASE_URL}/sign_in'
    sign_in_data = {
        'email': 'testuser2@example.com',
        'password': 'wrongpassword'
    }
    
    response = requests.get(sign_in_url, json=sign_in_data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'error' in response_data, "Отсутствует поле 'error' в ответе"
    assert response_data['error'] == True, "Ожидалось error=True для неверного пароля"
    my_print("✓ Неверный пароль обработан корректно")
    
    my_print("\n✅ Тест авторизации с неверным паролем пройден!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_sign_in_nonexistent_user():
    """
    Тест авторизации несуществующего пользователя
    """
    sign_in_url = f'{BASE_URL}/sign_in'
    sign_in_data = {
        'email': 'nonexistent@example.com',
        'password': 'anypassword'
    }
    
    response = requests.get(sign_in_url, json=sign_in_data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'error' in response_data, "Отсутствует поле 'error' в ответе"
    assert response_data['error'] == True, "Ожидалось error=True для несуществующего пользователя"
    my_print("✓ Несуществующий пользователь обработан корректно")
    
    my_print("\n✅ Тест авторизации несуществующего пользователя пройден!")


if __name__ == "__main__":
    my_print("=" * 50)
    my_print("Запуск теста успешной авторизации")
    my_print("=" * 50)
    test_sign_in_success()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста авторизации с неверным паролем")
    my_print("=" * 50)
    test_sign_in_wrong_password()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста авторизации несуществующего пользователя")
    my_print("=" * 50)
    test_sign_in_nonexistent_user()