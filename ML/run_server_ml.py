#!/usr/bin/env python3
"""
Скрипт для запуска HTTP сервера
"""
import uvicorn
import sys
import os
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from util import parse_args, get_from_config, MLPath


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    with open(MLPath('configs/active_config.yaml')) as f:
      config = yaml.safe_load(f)

    PORT = args.get('port', config.get('server', {}).get('port', 8081))
    HOST = args.get('host', config.get('server', {}).get('host', '0.0.0.0'))
    RELOAD = args.get('reload', config.get('server', {}).get('reload', True))

    print("Запуск HTTP сервера на FastAPI...")
    print(f"Сервер будет доступен по адресу: {HOST}:{PORT}")
    print(f"Документация API: {HOST}:{PORT}/docs")
    print("Для остановки сервера нажмите Ctrl+C")
    print("-" * 50)
    
    uvicorn.run(
        "main_ml:app",
        host=HOST,
        port=PORT,
        reload=RELOAD
    )