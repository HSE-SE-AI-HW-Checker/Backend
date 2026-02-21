import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.server import Server
from tests.utils_for_tests import logger


def test_me_endpoint(client):
    """
    Тест эндпоинта /me с использованием TestClient
    """
    # 1. Регистрация пользователя
    sign_up_data = {
        'username': 'TestUserMe',
        'email': 'testuserme@example.com',
        'password': 'securepassword123'
    }
    response = client.post("/sign_up", json=sign_up_data)
    
    # Если пользователь уже существует, пробуем войти
    if response.status_code != 200 or response.json().get('error'):
        sign_in_data = {
            'email': 'testuserme@example.com',
            'password': 'securepassword123'
        }
        response = client.post("/sign_in", json=sign_in_data)
    
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens['access_token']
    
    # 2. Запрос к /me с токеном
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get("/me", headers=headers)
    
    assert response.status_code == 200
    logger.info("✓ Статус код 200")
    
    user_data = response.json()
    assert user_data['email'] == 'testuserme@example.com'
    assert user_data['username'] == 'TestUserMe'
    assert 'user_id' in user_data
    logger.info("✓ Данные пользователя корректны")
    
    # 3. Запрос к /me без токена
    response = client.get("/me")
    assert response.status_code == 401
    logger.info("✓ Запрос без токена отклонен (401)")
    
    logger.info("\n✅ Тест /me пройден успешно!")

if __name__ == "__main__":
    # Для запуска напрямую нужно создать клиент вручную
    from src.core.server import Server
    server = Server(['config=testing'])
    with TestClient(server.app) as client:
        test_me_endpoint(client)