#!/usr/bin/env python3
"""
Скрипт для запуска HTTP сервера.
"""
import uvicorn
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.helpers import parse_args
from src.core.config_manager import get_from_config

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    PORT = args.get('port', get_from_config('port'))
    HOST = args.get('host', get_from_config('host'))
    RELOAD = args.get('reload', get_from_config('reload'))

    print("Запуск HTTP сервера на FastAPI...")
    print(f"Сервер будет доступен по адресу: {HOST}:{PORT}")
    print(f"Документация API: http://{HOST}:{PORT}/docs")
    print("Для остановки сервера нажмите Ctrl+C")
    print("-" * 50)
    
    uvicorn.run(
        "src.main:app",
        host=HOST,
        port=int(PORT),
        reload=RELOAD
    )