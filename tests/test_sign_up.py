import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from util import get_from_config, get_url_from_config
from test_utils import with_test_server

CONFIG = 'testing_config.json'

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
        print("✓ Статус код 200")

        assert response.json() == {'message': 'Пользователь зарегистрирован', 'error': False}
        print("✓ Ответ сервера корректен")
        
        print("\n✅ Все тесты пройдены успешно!")

    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу")
        raise
    except AssertionError as e:
        print(f"❌ Тест провален: {e}")
        raise

if __name__ == "__main__":
    test_sign_up()