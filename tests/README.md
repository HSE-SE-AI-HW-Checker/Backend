# Тестирование сервера

## Декоратор `@with_test_server`

Для удобного тестирования HTTP эндпоинтов создан декоратор `@with_test_server`, который автоматически запускает тестовый сервер в отдельном процессе перед выполнением теста и останавливает его после завершения.

### Преимущества использования multiprocessing

Декоратор использует `multiprocessing` вместо `threading`, что решает проблему с SQLite:
- Каждый процесс имеет свое собственное соединение к базе данных
- Нет конфликтов при работе с SQLite из разных потоков
- Полная изоляция тестовой среды

### Использование

```python
from test_utils import with_test_server

@with_test_server(config='testing_config.json', startup_delay=3)
def test_my_endpoint():
    response = requests.get('http://localhost:1234/health')
    assert response.status_code == 200
```

### Параметры декоратора

- `config` (str): имя конфигурационного файла (по умолчанию `'testing_config.json'`)
- `startup_delay` (int): задержка в секундах для запуска сервера (по умолчанию `2`)

### Примеры тестов

#### Тест регистрации пользователя

```python
@with_test_server(config='testing_config.json', startup_delay=2, max_wait=10)
def test_sign_up():
    url = f'{get_url_from_config(CONFIG)}/sign_up'
    data = {'username': 'Andrew', 'email': 'andrew@gmail.com', 'password': '123456'}
    response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 200
    assert response.json() == {'message': 'Пользователь зарегистрирован', 'error': False}
```

#### Тест health check

```python
@with_test_server(config='testing_config.json', startup_delay=2, max_wait=10)
def test_health_endpoint():
    response = requests.get(f'{BASE_URL}/health')
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
```

#### Тест авторизации

```python
@with_test_server(config='testing_config.json', startup_delay=2, max_wait=10)
def test_sign_in_success():
    # Регистрация
    sign_up_url = f'{BASE_URL}/sign_up'
    sign_up_data = {'username': 'TestUser', 'email': 'test@example.com', 'password': 'pass123'}
    requests.post(sign_up_url, json=sign_up_data, headers=HEADERS)
    
    # Авторизация
    sign_in_url = f'{BASE_URL}/sign_in'
    sign_in_data = {'email': 'test@example.com', 'password': 'pass123'}
    response = requests.get(sign_in_url, json=sign_in_data, headers=HEADERS)
    
    assert response.status_code == 200
    assert response.json()['error'] == False
```

#### Тест логирования

```python
@with_test_server(config='testing_config.json', startup_delay=2, max_wait=10)
def test_log_endpoint():
    url = f'{BASE_URL}/log'
    data = {'message': 'Тестовое сообщение'}
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200
    assert response.json()['message'] == 'Сообщение записано в лог'
```

#### Тест отправки данных

```python
@with_test_server(config='testing_config.json', startup_delay=2, max_wait=10)
def test_submit_git_link():
    url = f'{BASE_URL}/submit'
    data = {'data': 'https://github.com/user/repo.git', 'data_type': 0}
    response = requests.post(url, json=data, headers=HEADERS)
    
    assert response.status_code == 200
    assert response.json()['message'] == 'Данные получены сервером'
```

### Запуск тестов

Каждый тестовый файл можно запустить отдельно:

```bash
python tests/test_health_check.py
python tests/test_sign_up.py
python tests/test_sign_in.py
python tests/test_log.py
python tests/test_submit.py
```

Или запустить все тесты сразу:

```bash
python tests/run_all_tests.py
```

**Автоматическое обнаружение тестов**: Скрипт `run_all_tests.py` автоматически находит все файлы `test_*.py` в директории `tests/` и запускает все функции, начинающиеся с `test_`. Это означает, что при добавлении новых тестов не нужно вручную регистрировать их в `run_all_tests.py` - они будут обнаружены автоматически.

### Конфигурация тестового сервера

Настройки тестового сервера находятся в файле `configs/testing_config.json`:

```json
{
    "logger_implementation": "TestingLogger",
    "log_file": "tests/output/log.txt",
    "database_implementation": "SQLite",
    "host": "localhost",
    "port": 1234,
    "reload": true,
    "drop_db": true
}
```

Параметр `drop_db: true` обеспечивает чистую базу данных для каждого запуска тестов.

### Структура тестов

```
tests/
├── README.md                 # Документация
├── test_utils.py            # Утилиты для тестирования (декоратор)
├── test_health_check.py     # Тесты служебных эндпоинтов (/health, /info)
├── test_sign_up.py          # Тесты регистрации (/sign_up)
├── test_sign_in.py          # Тесты авторизации (/sign_in)
├── test_log.py              # Тесты логирования (/log)
├── test_submit.py           # Тесты отправки данных (/submit)
├── run_all_tests.py         # Запуск всех тестов
├── start_test_server.py     # Ручной запуск тестового сервера
└── output/                  # Выходные файлы (логи и т.д.)
```

### Важные замечания

1. **Изоляция процессов**: Каждый тест с декоратором запускает сервер в отдельном процессе, что обеспечивает полную изоляцию
2. **Автоматическая очистка**: Сервер автоматически останавливается после завершения теста, даже если тест упал с ошибкой
3. **Задержка запуска**: Параметр `startup_delay` важен для того, чтобы сервер успел полностью запуститься перед выполнением теста
4. **База данных**: При `drop_db: true` база данных пересоздается при каждом запуске сервера