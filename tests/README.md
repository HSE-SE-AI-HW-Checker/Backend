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
@with_test_server(config='testing_config.json', startup_delay=3)
def test_registration():
    url = 'http://localhost:1234/register'
    data = {'username': 'Andrew', 'email': 'andrew@gmail.com', 'password': '123456'}
    response = requests.post(url, json=data)
    
    assert response.status_code == 200
    assert response.json() == {'message': 'Пользователь зарегистрирован', 'error': False}
```

#### Тест health check

```python
@with_test_server(config='testing_config.json', startup_delay=3)
def test_health_endpoint():
    response = requests.get('http://localhost:1234/health')
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
```

### Запуск тестов

Каждый тестовый файл можно запустить отдельно:

```bash
python tests/test_authorization.py
python tests/test_health_check.py
```

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
├── test_authorization.py    # Тесты авторизации/регистрации
├── test_health_check.py     # Тесты служебных эндпоинтов
├── start_test_server.py     # Ручной запуск тестового сервера
└── output/                  # Выходные файлы (логи и т.д.)
```

### Важные замечания

1. **Изоляция процессов**: Каждый тест с декоратором запускает сервер в отдельном процессе, что обеспечивает полную изоляцию
2. **Автоматическая очистка**: Сервер автоматически останавливается после завершения теста, даже если тест упал с ошибкой
3. **Задержка запуска**: Параметр `startup_delay` важен для того, чтобы сервер успел полностью запуститься перед выполнением теста
4. **База данных**: При `drop_db: true` база данных пересоздается при каждом запуске сервера