import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import logger


def test_sign_in_success(client):
    """
    Тест успешной авторизации пользователя
    """
    # Сначала регистрируем пользователя
    sign_up_data = {
        'username': 'TestUser',
        'email': 'testuser@example.com',
        'password': 'securepassword123'
    }
    
    sign_up_response = client.post('/sign_up', json=sign_up_data)
    assert sign_up_response.status_code == 200, "Не удалось зарегистрировать пользователя"
    logger.info("✓ Пользователь зарегистрирован")
    
    # Теперь пытаемся авторизоваться
    sign_in_data = {
        'email': 'testuser@example.com',
        'password': 'securepassword123'
    }
    
    response = client.post('/sign_in', json=sign_in_data)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    assert 'message' in response_data, "Отсутствует поле 'message' в ответе"
    assert 'error' in response_data, "Отсутствует поле 'error' в ответе"
    assert response_data['error'] == False, "Ожидалось error=False для успешной авторизации"
    assert 'access_token' in response_data, "Отсутствует access_token"
    assert 'refresh_token' in response_data, "Отсутствует refresh_token"
    assert response_data['token_type'] == 'bearer', "Неверный тип токена"
    logger.info("✓ Авторизация прошла успешно, токены получены")
    
    logger.info("\n✅ Тест успешной авторизации пройден!")


def test_sign_in_wrong_password(client):
    """
    Тест авторизации с неверным паролем
    """
    # Сначала регистрируем пользователя
    sign_up_data = {
        'username': 'TestUser2',
        'email': 'testuser2@example.com',
        'password': 'correctpassword'
    }
    
    sign_up_response = client.post('/sign_up', json=sign_up_data)
    assert sign_up_response.status_code == 200, "Не удалось зарегистрировать пользователя"
    logger.info("✓ Пользователь зарегистрирован")
    
    # Пытаемся авторизоваться с неверным паролем
    sign_in_data = {
        'email': 'testuser2@example.com',
        'password': 'wrongpassword'
    }
    
    response = client.post('/sign_in', json=sign_in_data)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    assert 'error' in response_data, "Отсутствует поле 'error' в ответе"
    assert response_data['error'] == True, "Ожидалось error=True для неверного пароля"
    logger.info("✓ Неверный пароль обработан корректно")
    
    logger.info("\n✅ Тест авторизации с неверным паролем пройден!")


def test_sign_in_nonexistent_user(client):
    """
    Тест авторизации несуществующего пользователя
    """
    sign_in_data = {
        'email': 'nonexistent@example.com',
        'password': 'anypassword'
    }
    
    response = client.post('/sign_in', json=sign_in_data)
    
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
    logger.info("✓ Статус код 200")
    
    response_data = response.json()
    assert 'error' in response_data, "Отсутствует поле 'error' в ответе"
    assert response_data['error'] == True, "Ожидалось error=True для несуществующего пользователя"
    logger.info("✓ Несуществующий пользователь обработан корректно")
    
    logger.info("\n✅ Тест авторизации несуществующего пользователя пройден!")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Запуск теста успешной авторизации")
    logger.info("=" * 50)
    test_sign_in_success()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста авторизации с неверным паролем")
    logger.info("=" * 50)
    test_sign_in_wrong_password()
    
    logger.info("\n" + "=" * 50)
    logger.info("Запуск теста авторизации несуществующего пользователя")
    logger.info("=" * 50)
    test_sign_in_nonexistent_user()