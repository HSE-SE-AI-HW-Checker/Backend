"""
Точка входа для Backend приложения.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .core.server import Server
import sys

server_instance = Server(sys.argv[1:])
app = server_instance.app

@app.get("/info")
async def info():
    """
    Эндпоинт с информацией о сервере.
    
    Returns:
        dict: Информация о сервере
    """
    return {
        "server": "FastAPI",
        "version": "0.1.0",
        "description": "Простой HTTP сервер для демонстрации",
        "endpoints": [
            "/",
            "/info"
        ]
    }