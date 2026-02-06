import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from util import get_from_config
from tests.utils_for_tests import with_test_server

CONFIG = 'testing_config.json'

HOST = get_from_config("host", CONFIG)
PORT = get_from_config("port", CONFIG)
BASE_URL = f'http://{HOST}:{PORT}'


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_health_endpoint():
    """
    Тест эндпоинта проверки здоровья сервера
    """
    response = requests.get(f'{BASE_URL}/health')
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    print("✓ Статус код 200")
    
    data = response.json()
    assert 'status' in data, "Отсутствует поле 'status' в ответе"
    assert data['status'] == 'healthy', f"Ожидался статус 'healthy', получен {data['status']}"
    print("✓ Статус сервера: healthy")
    
    assert 'timestamp' in data, "Отсутствует поле 'timestamp' в ответе"
    print("✓ Timestamp присутствует")
    
    assert 'version' in data, "Отсутствует поле 'version' в ответе"
    print("✓ Version присутствует")
    
    print("\n✅ Все тесты health check пройдены успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_info_endpoint():
    """
    Тест информационного эндпоинта
    """
    response = requests.get(f'{BASE_URL}/info')
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    print("✓ Статус код 200")
    
    data = response.json()
    assert 'server' in data, "Отсутствует поле 'server' в ответе"
    assert 'version' in data, "Отсутствует поле 'version' в ответе"
    assert 'endpoints' in data, "Отсутствует поле 'endpoints' в ответе"
    print("✓ Все обязательные поля присутствуют")
    
    print("\n✅ Все тесты info endpoint пройдены успешно!")


if __name__ == "__main__":
    print("=" * 50)
    print("Запуск тестов health check")
    print("=" * 50)
    test_health_endpoint()
    
    print("\n" + "=" * 50)
    print("Запуск тестов info endpoint")
    print("=" * 50)
    test_info_endpoint()