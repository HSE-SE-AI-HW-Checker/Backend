import requests
import json
import datetime


def send_submit_request():
    url = "http://localhost:8080/"
    
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
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "data": "https://github.com/BaGGeRTeaMYT/HSETestingHomeworks",
        "requirements": {
            "Проект собирается без ошибок одной командой (например, `make`, `mvn test`, `npm test`)": 1,
            "В репозитории присутствует README с инструкцией по запуску и примером использования": 1,
            "Реализована проверка входных данных и обработка ошибок без аварийного завершения приложения": 1,
            "Критическая бизнес-логика покрыта автоматическими тестами (unit и/или integration)": 1,
            "В проекте настроен CI (GitHub Actions/GitLab CI) для сборки и запуска тестов при каждом push": 1,
            "Логирование реализовано через стандартный механизм/библиотеку и не использует `print` в продакшн-коде": 1,
            "В проекте соблюдается единый стиль кода и присутствует конфигурация линтера/форматтера": 1,
            "Секреты (ключи, токены, пароли) не хранятся в репозитории в открытом виде": 1,
            "API проекта документировано (OpenAPI/Swagger или Markdown-описание эндпоинтов)": 1,
            "Компоненты проекта разделены по слоям (например, controller/service/repository) и не содержат циклических зависимостей": 1,

            "Приложение должно работать на сервере с 128 ГБ ОЗУ": 1,  # should be deleted
            "Интерфейс приложения должен быть красивым и современным": 1,  # should be deleted
            "Код должен быть написан исключительно ночью для повышения качества": 1,  # should be deleted
            "В радуге 7 цветов": 1,  # should be deleted
            "Сложение — арифметическая операция над двумя числами": 1,  # should be deleted
            "Все комментарии в коде должны быть написаны в стихотворной форме": 1,  # should be deleted
            "Приложение должно нравиться всем пользователям без исключений": 1,  # should be deleted
        },

        "data_type": 0,
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