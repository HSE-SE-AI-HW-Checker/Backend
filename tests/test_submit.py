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
def test_submit_git_link():
    """
    Тест отправки данных типа 0 (ссылка на git)
    """
    url = f'{BASE_URL}/submit'
    data = {
        'data': 'https://github.com/user/repo.git',
        'data_type': 0
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    my_print("✓ Ответ сервера корректен")
    
    my_print("\n✅ Тест отправки git ссылки пройден успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_submit_archive():
    """
    Тест отправки данных типа 1 (архив)
    """
    url = f'{BASE_URL}/submit'
    data = {
        'data': 'base64_encoded_archive_data_here',
        'data_type': 1
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    my_print("✓ Ответ сервера корректен")
    
    my_print("\n✅ Тест отправки архива пройден успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_submit_file_format():
    """
    Тест отправки данных типа 2 (формат с окошком на каждый файл)
    """
    url = f'{BASE_URL}/submit'
    data = {
        'data': '{"file1.py": "content1", "file2.py": "content2"}',
        'data_type': 2
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    my_print("✓ Ответ сервера корректен")
    
    my_print("\n✅ Тест отправки файлового формата пройден успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_submit_unknown_type():
    """
    Тест отправки данных с неизвестным типом
    """
    url = f'{BASE_URL}/submit'
    data = {
        'data': 'some_data',
        'data_type': 999
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    my_print("✓ Неизвестный тип данных обработан корректно")
    
    my_print("\n✅ Тест отправки неизвестного типа данных пройден успешно!")


@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_submit_empty_data():
    """
    Тест отправки пустых данных
    """
    url = f'{BASE_URL}/submit'
    data = {
        'data': '',
        'data_type': 0
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    my_print("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Данные получены сервером'
    my_print("✓ Пустые данные обработаны корректно")
    
    my_print("\n✅ Тест отправки пустых данных пройден успешно!")


if __name__ == "__main__":
    my_print("=" * 50)
    my_print("Запуск теста отправки git ссылки")
    my_print("=" * 50)
    test_submit_git_link()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста отправки архива")
    my_print("=" * 50)
    test_submit_archive()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста отправки файлового формата")
    my_print("=" * 50)
    test_submit_file_format()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста отправки неизвестного типа")
    my_print("=" * 50)
    test_submit_unknown_type()
    
    my_print("\n" + "=" * 50)
    my_print("Запуск теста отправки пустых данных")
    my_print("=" * 50)
    test_submit_empty_data()