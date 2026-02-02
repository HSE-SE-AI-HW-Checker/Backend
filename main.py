from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from server import Server
import sys

server_instance = Server(sys.argv[1:])
app = server_instance.app

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Главная страница сервера
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug page</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .endpoint {
                background-color: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            code {
                background-color: #e9ecef;
                padding: 2px 4px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ты кто?</h1>
            <p>Доступные эндпоинты:</p>
            
            <div class="endpoint">
                <h3><code>GET /</code></h3>
                <p>Главная страница (текущая страница)</p>
            </div>
            
            <div class="endpoint">
                <h3><code>GET /hello</code></h3>
                <p>Возвращает приветственное сообщение</p>
            </div>
            
            <div class="endpoint">
                <h3><code>GET /status</code></h3>
                <p>Проверяет статус сервера</p>
            </div>
            
            <div class="endpoint">
                <h3><code>GET /info</code></h3>
                <p>Возвращает информацию о сервере</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/info")
async def info():
    """
    Эндпоинт с информацией о сервере
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

# if __name__ == "__main__":
#     server_instance.run()