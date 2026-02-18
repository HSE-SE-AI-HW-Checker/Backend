# Backend Server

Backend сервер для проверки домашних заданий с использованием FastAPI.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

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
python run_server.py host=0.0.0.0 port=8080
```

Сервер будет доступен по адресу: http://localhost:8000

## API Endpoints

### Основные эндпоинты:
- `GET /health` - Проверка здоровья сервера
- `POST /log` - Запись в лог
- `POST /sign_up` - Регистрация пользователя
- `POST /sign_in` - Авторизация пользователя
- `POST /submit` - Отправка домашнего задания

Подробная документация API доступна в [API_USAGE.md](API_USAGE.md)

## Интерактивная документация

После запуска сервера доступна автоматическая документация:
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

## Конфигурация

Сервер использует YAML файлы конфигурации:
- `configs/default.yaml` - Разработка
- `configs/testing.yaml` - Тестирование
- `configs/production.yaml` - Продакшн
- `config.yaml` - Активная конфигурация (в корне)

### Параметры конфигурации:
```yaml
log_file_path: logs/server.log       # Путь к логам
log_file_mod: a                      # (a)ppend, (w)rite
log_to_console: true                 # стоит ли писать логи в консоль
log_level: WARNING                   # log_level из стандартного модуля logging
database_implementation: SQLite      # Класс БД
host: localhost                      # Хост
port: 8000                           # Порт
reload: true                         # Автоперезагрузка
drop_db: false                       # Удалять БД при запуске
```

## Тестирование

Запуск тестов:
```bash
python tests/run_all_tests.py
```

## Разработка

### Добавление нового эндпоинта
1. Добавьте обработчик в [`src/core/server.py`](src/core/server.py) в метод `_setup_handlers()`
2. Определите модели данных с использованием Pydantic
3. Обновите документацию в [`API_USAGE.md`](API_USAGE.md)

### Добавление новой конфигурации
1. Создайте новый YAML файл в директории `configs/`
2. Используйте его: `python run_server.py config=your_config`

## Зависимости

Основные зависимости:
- FastAPI - Веб-фреймворк
- Uvicorn - ASGI сервер
- Pydantic - Валидация данных
- PyYAML - Работа с YAML
- Requests - HTTP клиент

## Troubleshooting

### Порт уже занят
```bash
python run_server.py port=8001
```

### База данных заблокирована
```bash
rm data/AppUsers.db
python run_server.py
```

### Проблемы с импортами
Убедитесь, что вы находитесь в корневой директории Backend:
```bash
cd Backend
python run_server.py
```

## Лицензия

MIT License