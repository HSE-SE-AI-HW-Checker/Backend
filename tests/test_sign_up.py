import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from src.core.config_manager import get_from_config, get_url_from_config
from tests.utils_for_tests import with_test_server, my_print

CONFIG = 'testing'

URL = f'{get_url_from_config(CONFIG)}/sign_up'
DATA = {'username': 'Andrew', 'email': 'andrew@gmail.com', 'password': '123456'}
HEADERS = {'Content-Type': 'application/json'}

@with_test_server(config=CONFIG, startup_delay=2, max_wait=10)
def test_sign_up():
    """
    Тест регистрации пользователя
    """
    response = requests.post(URL, json=DATA, headers=HEADERS)

    try:
        assert response.status_code == 200
        my_print("✓ Статус код 200")

        response_data = response.json()
        assert response_data['message'] == 'Пользователь зарегистрирован'
        assert response_data['error'] is False
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
        assert 'token_type' in response_data
        assert response_data['token_type'] == 'bearer'
        my_print("✓ Ответ сервера корректен, токены получены")
        
        my_print("\n✅ Все тесты пройдены успешно!")

    except requests.exceptions.ConnectionError:
        my_print("❌ Ошибка подключения к серверу")
        raise
    except AssertionError as e:
        my_print(f"❌ Тест провален: {e}")
        raise

if __name__ == "__main__":
    test_sign_up()