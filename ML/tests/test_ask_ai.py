import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

HEADERS = {'Content-Type': 'application/json'}

def test_ask_ai():
    response = requests.post(
        "http://localhost:8000/ask_ai",
        json={"prompt": "Some of the best dishes for breakfast are: "},
        headers=HEADERS
    )

    assert response.status_code == 200
    print(f"{response.json().get('message')}")


if __name__ == "__main__":
    test_ask_ai()