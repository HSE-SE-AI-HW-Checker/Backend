#!/usr/bin/env python3
import uvicorn
import sys
import os
from util import parse_args, get_from_config

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    PORT = args.get('port', get_from_config('port'))
    HOST = args.get('host', get_from_config('host'))
    RELOAD = args.get('reload', get_from_config('reload'))

    print("Запуск HTTP сервера на FastAPI...")
    print(f"Сервер будет доступен по адресу: {HOST}:{PORT}")
    print(f"Документация API: {HOST}:{PORT}/docs")
    print("Для остановки сервера нажмите Ctrl+C")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD
    )