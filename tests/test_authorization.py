import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from util import get_from_config

CONFIG = 'testing_config.json'

URL = f'http://{get_from_config('host', )}:{get_from_config('port', 'testing_config.json')}/register'
DATA = {'username': 'Andrew', 'email': 'andrew@gmail.com', 'password': '123456'}
HEADERS = {'Content-Type': 'application/json'}

def test():
    response = requests.post(URL, json=DATA, headers=HEADERS)

    try:
        assert response.status_code == 200
        print("OK")

        assert response.json() == {'message': 'Пользователь зарегистрирован', 'error': False}
        print("OK")

    except requests.exceptions.ConnectionError:
        print("Connection failed")

if __name__ == "__main__":
    test()