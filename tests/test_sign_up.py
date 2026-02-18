import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import with_test_server, logger

CONFIG = 'testing'

DATA = {'username': 'Andrew', 'email': 'andrew@gmail.com', 'password': '123456'}

@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_sign_up(client):
    """
    Тест регистрации пользователя
    """
    response = client.post('/sign_up', json=DATA)

    try:
        assert response.status_code == 200
        logger.info("✓ Статус код 200")

        response_data = response.json()
        assert response_data['message'] == 'Пользователь зарегистрирован'
        assert response_data['error'] is False
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
        assert 'token_type' in response_data
        assert response_data['token_type'] == 'bearer'
        logger.info("✓ Ответ сервера корректен, токены получены")
        
        logger.info("\n✅ Все тесты пройдены успешно!")

    except AssertionError as e:
        logger.error(f"❌ Тест провален: {e}")
        raise

if __name__ == "__main__":
    test_sign_up()