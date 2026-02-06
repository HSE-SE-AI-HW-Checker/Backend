import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from util import get_url_from_config
from tests.utils_for_tests import with_test_server, my_print

CONFIG = 'testing_config.json'

BASE_URL = get_url_from_config(CONFIG)
HEADERS = {'Content-Type': 'application/json'}


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_log_endpoint():
    """
    Тест эндпоинта записи сообщения в лог
    """
    url = f'{BASE_URL}/log'
    data = {'message': 'Тестовое сообщение для логирования'}
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Сообщение записано в лог', f"Неожиданное сообщение: {response_data['message']}"
    my_print("✓ Ответ сервера корректен")
    
    my_print("\n✅ Все тесты log endpoint пройдены успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_log_endpoint_empty_message():
    """
    Тест эндпоинта записи пустого сообщения в лог
    """
    url = f'{BASE_URL}/log'
    data = {'message': ''}
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200 для пустого сообщения")
    
    response_data = response.json()
    assert response_data['message'] == 'Сообщение записано в лог'
    my_print("✓ Пустое сообщение обработано корректно")
    
    my_print("\n✅ Тест пустого сообщения пройден успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_log_endpoint_long_message():
    """
    Тест эндпоинта записи длинного сообщения в лог
    """
    url = f'{BASE_URL}/log'
    long_message = 'A' * 1000  # Длинное сообщение из 1000 символов
    data = {'message': long_message}
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200 для длинного сообщения")
    
    response_data = response.json()
    assert response_data['message'] == 'Сообщение записано в лог'
    my_print("✓ Длинное сообщение обработано корректно")
    
    my_print("\n✅ Тест длинного сообщения пройден успешно!")


if __name__ == "__main__":
    my_print("=" * 50)
    my_print("Запуск тестов log endpoint")
    my_print("=" * 50)
    test_log_endpoint()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста пустого сообщения")
    my_print("=" * 50)
    test_log_endpoint_empty_message()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста длинного сообщения")
    my_print("=" * 50)
    test_log_endpoint_long_message()