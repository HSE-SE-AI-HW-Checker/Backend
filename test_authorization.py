import requests
from util import get_from_config
from server import Server

URL = f'http://{get_from_config('host', 'testing_config.json')}:{get_from_config('port', 'testing_config.json')}/register'
DATA = {'username': 'Andrew', 'email': 'andrew@gmail.com', 'password': '123456'}
HEADERS = {'Content-Type': 'application/json'}

def test():
    server = Server(["config=testing_config.json"])
    server.run()

    response = requests.post(URL, json=DATA, headers=HEADERS)

    assert response.status_code == 200
    print("OK")

    assert response.json() == {'message': ''}

test()