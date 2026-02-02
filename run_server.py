#!/usr/bin/env python3
"""
Скрипт для запуска HTTP сервера
"""
import uvicorn
import sys
import os

PORT=8080

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Запуск HTTP сервера на FastAPI...")
    print(f"Сервер будет доступен по адресу: http://localhost:{PORT}")
    print(f"Документация API: http://localhost:{PORT}/docs")
    print("Для остановки сервера нажмите Ctrl+C")
    print("-" * 50)
    
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)