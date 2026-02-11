# Backend Server

Backend сервер для проверки домашних заданий с использованием FastAPI.

## Структура проекта

```
Backend/
├── src/                      # Исходный код
│   ├── core/                # Основные компоненты
│   │   ├── server.py        # Основной сервер
│   │   ├── database_manager.py  # Менеджер БД
│   │   └── config_manager.py    # Менеджер конфигурации
│   ├── utils/               # Утилиты
│   │   ├── logger.py        # Логирование
│   │   ├── helpers.py       # Вспомогательные функции
│   │   ├── validators.py    # Валидация данных
│   │   └── exceptions.py    # Кастомные исключения
│   ├── security/            # Безопасность
│   │   └── encryptors.py    # Шифрование
│   ├── models/              # Модели данных
│   │   └── config.py        # Модели конфигурации
│   └── main.py              # Точка входа
├── configs/                 # Конфигурационные файлы
│   ├── default.yaml         # Конфигурация по умолчанию
│   ├── testing.yaml         # Конфигурация для тестов
│   └── production.yaml      # Продакшн конфигурация
├── data/                    # База данных
├── logs/                    # Файлы логов
├── tests/                   # Тесты
├── config.yaml              # Активная конфигурация
├── run_server.py            # Скрипт запуска
├── requirements.txt         # Зависимости
├── pyproject.toml           # Метаданные проекта
├── ARCHITECTURE.md          # Архитектура проекта
└── API_USAGE.md             # Документация API
```

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
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
- `GET /info` - Информация о сервере
- `POST /log` - Запись в лог
- `POST /sign_up` - Регистрация пользователя
- `POST /sign_in` - Авторизация пользователя
- `POST /submit` - Отправка домашнего задания

Подробная документация API доступна в [API_USAGE.md](API_USAGE.md)

## Интерактивная документация

После запуска сервера доступна автоматическая документация:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Конфигурация

Сервер использует YAML файлы конфигурации:
- `configs/default.yaml` - Разработка
- `configs/testing.yaml` - Тестирование
- `configs/production.yaml` - Продакшн
- `config.yaml` - Активная конфигурация (в корне)

### Параметры конфигурации:
```yaml
logger_implementation: SimpleLogger  # Класс логгера
log_file_path: logs/server.log      # Путь к логам
database_implementation: SQLite      # Класс БД
host: localhost                      # Хост
port: 8000                          # Порт
reload: true                        # Автоперезагрузка
drop_db: false                      # Удалять БД при запуске
```

## Тестирование

Запуск тестов:
```bash
cd tests
python run_all_tests.py
```

## Архитектура

Подробное описание архитектуры проекта доступно в [ARCHITECTURE.md](ARCHITECTURE.md)

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