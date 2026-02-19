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

## Аутентификация

API использует JWT (JSON Web Tokens) для аутентификации.
При успешной регистрации или входе возвращается пара токенов: `access_token` и `refresh_token`.

Для доступа к защищенным эндпоинтам необходимо передавать `access_token` в заголовке `Authorization`:
```
Authorization: Bearer <your_access_token>
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
  "error": false,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
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
  "error": false,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### User Profile (Protected)
Получение профиля текущего пользователя.

**Endpoint:** `GET /me`
**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "user_id": 1,
  "email": "john@example.com",
  "username": "john_doe"
}
```

### Logout (Protected)
Выход из системы (отзыв токена).

**Endpoint:** `POST /logout`
**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Выход выполнен",
  "success": true
}
```

### Submit Homework (Protected)
Отправка домашнего задания на проверку.

**Endpoint:** `POST /submit`
**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "data": "https://github.com/user/homework",
  "requirements": {
    "Check code style": 1,
    "Check logic": 1
  },
  "data_type": 0
}
```

**Data Types:**
- `0` - Ссылка на git-подобную систему
- `1` - Архив
- `2` - Формат с окошком на каждый файл

**Response:**
Ответ от ML сервера с результатами проверки.
```json
{
  "text": "Результат проверки...",
  "prompt": "Использованный промпт..."
}
```

## Примеры использования

### Python (requests)
```python
import requests

BASE_URL = 'http://localhost:8000'

# Регистрация
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
}
response = requests.post(f'{BASE_URL}/sign_up', json=user_data)
tokens = response.json()
access_token = tokens.get('access_token')
print("Tokens:", tokens)

# Получение профиля
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(f'{BASE_URL}/me', headers=headers)
print("Profile:", response.json())

# Отправка задания
submit_data = {
    "data": "https://github.com/user/homework",
    "requirements": {"style": 1},
    "data_type": 0
}
response = requests.post(f'{BASE_URL}/submit', json=submit_data, headers=headers)
print("Result:", response.json())
```

### cURL
```bash
# Регистрация и получение токена
curl -X POST http://localhost:8000/sign_up \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"secure_password"}'

# Использование токена
curl http://localhost:8000/me \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

## Конфигурация

Сервер использует YAML файлы конфигурации из директории `configs/`:

- `default.yaml` - Конфигурация по умолчанию для разработки
- `testing.yaml` - Конфигурация для тестирования
- `production.yaml` - Конфигурация для продакшена

Активная конфигурация: `config.yaml` в корне проекта.

## Интерактивная документация

После запуска сервера доступна автоматическая документация:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc