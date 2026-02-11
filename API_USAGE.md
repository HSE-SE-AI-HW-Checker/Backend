# API Usage Guide

Руководство по использованию Backend API для проверки домашних заданий.

## Запуск сервера

### Базовый запуск
```bash
python run_server.py
```

### Запуск с параметрами
```bash
# Указать порт
python run_server.py port=8080

# Указать хост
python run_server.py host=0.0.0.0

# Указать конфигурацию
python run_server.py config=production

# Комбинация параметров
python run_server.py host=0.0.0.0 port=8080 reload=true
```

## API Endpoints

### Health Check
Проверка состояния сервера.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### Server Info
Информация о сервере.

**Endpoint:** `GET /info`

**Response:**
```json
{
  "server": "FastAPI",
  "version": "0.1.0",
  "description": "Простой HTTP сервер для демонстрации",
  "endpoints": ["/", "/info"]
}
```

### Logging
Запись сообщения в лог.

**Endpoint:** `POST /log`

**Request Body:**
```json
{
  "message": "Текст сообщения для логирования"
}
```

**Response:**
```json
{
  "message": "Сообщение записано в лог"
}
```

### User Registration
Регистрация нового пользователя.

**Endpoint:** `POST /sign_up`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password"
}
```

**Response (Success):**
```json
{
  "message": "Пользователь зарегистрирован",
  "error": false
}
```

**Response (Error):**
```json
{
  "message": "Пользователь с таким email уже существует",
  "error": true
}
```

### User Login
Авторизация пользователя.

**Endpoint:** `POST /sign_in`

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "secure_password"
}
```

**Response (Success):**
```json
{
  "message": "",
  "error": false
}
```

**Response (Error - Email not found):**
```json
{
  "message": "Почта john@example.com не зарегистрирована",
  "error": true
}
```

**Response (Error - Wrong password):**
```json
{
  "message": "Неверный пароль",
  "error": true
}
```

### Submit Homework
Отправка домашнего задания на проверку.

**Endpoint:** `POST /submit`

**Request Body:**
```json
{
  "data": "Содержимое домашнего задания",
  "data_type": 0
}
```

**Data Types:**
- `0` - Ссылка на git-подобную систему
- `1` - Архив
- `2` - Формат с окошком на каждый файл

**Response:**
Ответ от ML сервера с результатами проверки.

## Примеры использования

### Python (requests)
```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# Регистрация
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
}
response = requests.post('http://localhost:8000/sign_up', json=user_data)
print(response.json())

# Авторизация
login_data = {
    "email": "john@example.com",
    "password": "secure_password"
}
response = requests.post('http://localhost:8000/sign_in', json=login_data)
print(response.json())
```

### cURL
```bash
# Health check
curl http://localhost:8000/health

# Регистрация
curl -X POST http://localhost:8000/sign_up \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"secure_password"}'

# Авторизация
curl -X POST http://localhost:8000/sign_in \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secure_password"}'
```

## Конфигурация

Сервер использует YAML файлы конфигурации из директории `configs/`:

- `default.yaml` - Конфигурация по умолчанию для разработки
- `testing.yaml` - Конфигурация для тестирования
- `production.yaml` - Конфигурация для продакшена

Активная конфигурация: `config.yaml` в корне проекта.

### Параметры конфигурации

```yaml
logger_implementation: SimpleLogger  # Класс логгера
log_file_path: logs/server.log      # Путь к файлу логов
database_implementation: SQLite      # Класс БД
host: localhost                      # Хост сервера
port: 8000                          # Порт сервера
reload: true                        # Автоперезагрузка
drop_db: false                      # Удалять БД при запуске
```

## Интерактивная документация

После запуска сервера доступна автоматическая документация:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Troubleshooting

### Порт уже занят
```bash
# Используйте другой порт
python run_server.py port=8001
```

### База данных заблокирована
```bash
# Удалите файл БД и перезапустите
rm data/AppUsers.db
python run_server.py
```

### Проблемы с импортами
```bash
# Убедитесь, что вы в корневой директории Backend
cd Backend
python run_server.py