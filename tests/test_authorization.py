import requests
from util import get_from_config

URL = f'http://{get_from_config('host')}:{get_from_config('port')}'
DATA = {'key1': 'value1', 'key2': 'value2'}
HEADERS = {'Content-Type': 'application/json'}

def test():
    response = requests.post(URL, json=DATA, headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {"message": "Пользователь зарегистрирован"}