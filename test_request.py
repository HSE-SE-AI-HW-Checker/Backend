import requests
import json
import datetime

def send_submit_request():
    url = "http://localhost:8080/"
    
    # Токен из вашего примера


    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJlbWFpbCI6ImFuZHJld0B5YW5kZXgucnUiLCJleHAiOjE3NzEyNzAwNzIsImlhdCI6MTc3MTI2ODI3MiwidHlwZSI6ImFjY2VzcyJ9.6h08B_NrjgWZ3CJxcE3mEgRMDxujaMa6ggXRMMUCaZc"
    
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "username": "Andrew",
        "email": "andrew@yandex.ru",
        "password": "12345678"
    }

    try:
        response = requests.post(url + 'sign_in', headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()

        if 'access_token' in response_data:
            token = response_data['access_token']
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Статус код: {e.response.status_code}")
            print(f"Тело ответа: {e.response.text}")
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON ответа")
        print(f"Тело ответа: {response.text}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "data": "https://github.com/BaGGeRTeaMYT/JavaZooHW",
        "data_type": 0
    }
    
    try:
        time_before = datetime.datetime.now()
        response = requests.post(url + 'submit', headers=headers, json=payload)
        response.raise_for_status()  # Проверка на ошибки HTTP (4xx, 5xx)
        
        response_data = response.json()
        
        time_after = datetime.datetime.now()
        print(f"Время выполнения запроса: {time_after - time_before}")
        if "text" in response_data:
            print(response_data["text"])
        else:
            print("Поле 'text' не найдено в ответе.")
            print("Полный ответ:", json.dumps(response_data, indent=2, ensure_ascii=False))
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Статус код: {e.response.status_code}")
            print(f"Тело ответа: {e.response.text}")
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON ответа")
        print(f"Тело ответа: {response.text}")

if __name__ == "__main__":
    send_submit_request()