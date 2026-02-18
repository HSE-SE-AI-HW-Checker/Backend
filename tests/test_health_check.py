import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import with_test_server, logger

CONFIG = 'testing'

@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_health_endpoint(client):
    """
    Тест эндпоинта проверки здоровья сервера
    """
    response = client.get('/health')
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    data = response.json()
    assert 'status' in data, "Отсутствует поле 'status' в ответе"
    assert data['status'] == 'healthy', f"Ожидался статус 'healthy', получен {data['status']}"
    logger.info("✓ Статус сервера: healthy")
    
    assert 'timestamp' in data, "Отсутствует поле 'timestamp' в ответе"
    logger.info("✓ Timestamp присутствует")
    
    assert 'version' in data, "Отсутствует поле 'version' в ответе"
    logger.info("✓ Version присутствует")
    
    logger.info("\n✅ Все тесты health check пройдены успешно!")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Запуск тестов health check")
    logger.info("=" * 50)
    test_health_endpoint()