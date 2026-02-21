import os
import sys
import time
import multiprocessing
import requests
from functools import wraps

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib
import inspect
import uvicorn
import logging
from src.core.config_manager import get_from_config
from src.utils.helpers import MLPath

# Настройка логгера
logger = logging.getLogger(__name__)

def get_auth_headers(client):
    """
    Регистрирует пользователя и возвращает заголовки с токеном
    """
    sign_up_data = {
        'username': 'TestUserAuth',
        'email': 'testuser_auth@example.com',
        'password': 'securepassword123'
    }
    
    response = client.post("/sign_up", json=sign_up_data)
    if response.status_code != 200:
        # Если пользователь уже существует, пробуем войти
        sign_in_data = {
            'email': 'testuser_auth@example.com',
            'password': 'securepassword123'
        }
        response = client.post("/sign_in", json=sign_in_data)
    
    data = response.json()
    token = data.get('access_token')
    
    return {
        'Authorization': f'Bearer {token}'
    }

def discover_tests(tests_dir):
    """
    Автоматическое обнаружение всех тестовых функций
    
    Ищет все файлы test_*.py в директории tests и находит в них
    все функции, начинающиеся с test_
    
    Returns:
        list: Список кортежей (имя_теста, функция_теста)
    """
    tests = []
    
    # Получаем список всех файлов в директории tests
    for filename in sorted(os.listdir(tests_dir)):
        # Ищем только файлы test_*.py
        if filename.startswith('test_') and filename.endswith('.py'):
            module_name = filename[:-3]  # Убираем .py
            
            try:
                # Импортируем модуль
                module = importlib.import_module(module_name)
                
                # Ищем все функции, начинающиеся с test_
                for name, obj in inspect.getmembers(module):
                    if name.startswith('test_') and inspect.isfunction(obj):
                        # Формируем читаемое имя теста
                        test_display_name = f"{module_name}.{name}"
                        tests.append((test_display_name, obj))
                        
            except Exception as e:
                logger.error(f"⚠️  Не удалось загрузить модуль {module_name}: {e}")
    
    return tests

def run_server(config_name, server_type='backend'):
    sys.argv.append(f'config={config_name}')
    
    HOST = get_from_config('host', config_name)
    PORT = get_from_config('port', config_name)
    RELOAD = get_from_config('reload', config_name)

    sys.path.append(str(MLPath()))

    uvicorn.run(
        "src.main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="error"
    )

def wait_for_server(host, port, timeout=10, check_interval=0.5):
    """
    Ожидание готовности сервера
    
    Args:
        host: хост сервера
        port: порт сервера
        timeout: максимальное время ожидания в секундах
        check_interval: интервал проверки в секундах
    
    Returns:
        True если сервер готов, False если превышен timeout
    """
    url = f"http://{host}:{port}/health"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass
        time.sleep(check_interval)
    
    return False

