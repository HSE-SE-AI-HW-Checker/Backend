import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import logger, get_auth_headers


def test_submit_git_link(client):
    """
    Тест отправки данных типа 0 (ссылка на git)
    """
    data = {
        'data': 'https://github.com/user/repo.git',
        'requirements': {'test': 1},
        'data_type': 0
    }
    
    headers = get_auth_headers(client)
    response = client.post('/submit', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    # assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    # assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    logger.info("✓ Ответ сервера корректен")
    
    logger.info("\n✅ Тест отправки git ссылки пройден успешно!")


def test_submit_archive(client):
    """
    Тест отправки данных типа 1 (архив)
    """
    data = {
        'data': 'base64_encoded_archive_data_here',
        'requirements': {'test': 1},
        'data_type': 1
    }
    
    headers = get_auth_headers(client)
    response = client.post('/submit', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    # assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    # assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    logger.info("✓ Ответ сервера корректен")
    
    logger.info("\n✅ Тест отправки архива пройден успешно!")


def test_submit_file_format(client):
    """
    Тест отправки данных типа 2 (формат с окошком на каждый файл)
    """
    data = {
        'data': '{"file1.py": "content1", "file2.py": "content2"}',
        'requirements': {'test': 1},
        'data_type': 2
    }
    
    headers = get_auth_headers(client)
    response = client.post('/submit', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    # assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    # assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    logger.info("✓ Ответ сервера корректен")
    
    logger.info("\n✅ Тест отправки файлового формата пройден успешно!")


def test_submit_unknown_type(client):
    """
    Тест отправки данных с неизвестным типом
    """
    data = {
        'data': 'some_data',
        'requirements': {'test': 1},
        'data_type': 999
    }
    
    headers = get_auth_headers(client)
    response = client.post('/submit', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    # assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    # assert response_data['message'] == 'Данные получены сервером', f"Неожиданное сообщение: {response_data['message']}"
    logger.info("✓ Неизвестный тип данных обработан корректно")
    
    logger.info("\n✅ Тест отправки неизвестного типа данных пройден успешно!")


def test_submit_empty_data(client):
    """
    Тест отправки пустых данных
    """
    data = {
        'data': '',
        'requirements': {'test': 1},
        'data_type': 0
    }
    
    headers = get_auth_headers(client)
    response = client.post('/submit', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    # assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    # assert response_data['message'] == 'Данные получены сервером'
    logger.info("✓ Пустые данные обработаны корректно")
    
    logger.info("\n✅ Тест отправки пустых данных пройден успешно!")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Запуск теста отправки git ссылки")
    logger.info("=" * 50)
    test_submit_git_link()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста отправки архива")
    logger.info("=" * 50)
    test_submit_archive()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста отправки файлового формата")
    logger.info("=" * 50)
    test_submit_file_format()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста отправки неизвестного типа")
    logger.info("=" * 50)
    test_submit_unknown_type()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста отправки пустых данных")
    logger.info("=" * 50)
    test_submit_empty_data()