## Установка и запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите сервер одним из способов:

   **Способ 1 (рекомендуемый):**
   ```bash
   source venv/bin/activate && python run_server.py
   ```
   
   **Способ 2:**
   ```bash
   source venv/bin/activate && python main.py
   ```

Сервер будет доступен по адресу: http://localhost:8000

## Доступные эндпоинты

### Основные эндпоинты:
- `GET /register` запрос на регистрацию пользователя
- `GET /authorize` запрос на авторизацию пользователя

 
## Примеры использования

### Получение списка товаров:
```bash
curl http://localhost:8000/items
```

### Фильтрация товаров по категории:
```bash
curl http://localhost:8000/items?category=Электроника
```

### Создание нового товара:
```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Смартфон", "description": "Новый смартфон", "price": 699.99, "category": "Электроника"}'
```

### Поиск:
```bash
curl http://localhost:8000/search?q=ноутбук
```

## Документация API

FastAPI автоматически генерирует интерактивную документацию:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

- `main.py` - Основной файл приложения с настройкой сервера
- `http_handler.py` - Обработчики HTTP запросов
- `run_server.py` - Скрипт для удобного запуска сервера с автоперезагрузкой
- `requirements.txt` - Зависимости проекта
- `README.md` - Документация проекта
- `venv/` - Виртуальное окружение Python