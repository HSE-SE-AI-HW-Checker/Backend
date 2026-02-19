import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import logger, get_auth_headers


def test_log_endpoint(client):
    """
    Тест эндпоинта записи сообщения в лог
    """
    data = {'message': 'Тестовое сообщение для логирования'}
    
    headers = get_auth_headers(client)
    response = client.post('/log', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert response_data['message'] == 'Сообщение записано в лог', f"Неожиданное сообщение: {response_data['message']}"
    logger.info("✓ Ответ сервера корректен")
    
    logger.info("\n✅ Все тесты log endpoint пройдены успешно!")


def test_log_endpoint_empty_message(client):
    """
    Тест эндпоинта записи пустого сообщения в лог
    """
    data = {'message': ''}
    
    headers = get_auth_headers(client)
    response = client.post('/log', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200 для пустого сообщения")
    
    response_data = response.json()
    assert response_data['message'] == 'Сообщение записано в лог'
    logger.info("✓ Пустое сообщение обработано корректно")
    
    logger.info("\n✅ Тест пустого сообщения пройден успешно!")


def test_log_endpoint_long_message(client):
    """
    Тест эндпоинта записи длинного сообщения в лог
    """
    long_message = 'A' * 1000  # Длинное сообщение из 1000 символов
    data = {'message': long_message}
    
    headers = get_auth_headers(client)
    response = client.post('/log', json=data, headers=headers)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200 для длинного сообщения")
    
    response_data = response.json()
    assert response_data['message'] == 'Сообщение записано в лог'
    logger.info("✓ Длинное сообщение обработано корректно")
    
    logger.info("\n✅ Тест длинного сообщения пройден успешно!")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Запуск тестов log endpoint")
    logger.info("=" * 50)
    test_log_endpoint()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста пустого сообщения")
    logger.info("=" * 50)
    test_log_endpoint_empty_message()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста длинного сообщения")
    logger.info("=" * 50)
    test_log_endpoint_long_message()