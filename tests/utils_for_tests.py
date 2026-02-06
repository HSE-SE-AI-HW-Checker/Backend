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
from util import get_from_config, MLPath

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
                print(f"⚠️  Не удалось загрузить модуль {module_name}: {e}")
    
    return tests

def run_server(config_name, server_type='backend'):
    sys.argv = ['', f'config={config_name}']
    
    HOST = get_from_config('host', config_name)
    PORT = get_from_config('port', config_name)
    RELOAD = get_from_config('reload', config_name)

    uvicorn.run(
        f"main_{server_type}:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="error"
    )
    

def run_server_process(config_name):
    """
    Функция для запуска сервера в отдельном процессе
    """
    sys.argv = ['', f'config={config_name}']
    
    HOST = get_from_config('host', config_name)
    PORT = get_from_config('port', config_name)
    RELOAD = get_from_config('reload', config_name)
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="error"  # Уменьшаем вывод логов
    )

def run_ml_server_process(config_name):
    """
    Функция для запуска сервера машинного обучения в отдельном процессе
    """
    sys.argv = ['', f'config={config_name}']
    
    HOST = get_from_config('host', config_name)
    PORT = get_from_config('port', config_name)
    
    sys.path.append(MLPath())

    uvicorn.run(
        "main_ml:app",
        host=HOST,
        port=PORT,
        log_level="error"  # Уменьшаем вывод логов
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


def with_test_server(config='testing_config.json', server_type='backend', startup_delay=5, max_wait=10):
    """
    Декоратор для запуска тестового сервера в отдельном процессе
    
    Args:
        config: имя конфигурационного файла
        startup_delay: начальная задержка в секундах перед проверкой готовности
        max_wait: максимальное время ожидания готовности сервера
    
    Использование:
        @with_test_server()
        def test_my_endpoint():
            response = requests.get('http://localhost:1234/health')
            assert response.status_code == 200
    """
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            HOST = get_from_config('host', config)
            PORT = get_from_config('port', config)
            
            # Создаем процесс для запуска сервера
            server_process = multiprocessing.Process(
                target=run_server,
                args=(config, server_type),
                daemon=True  # Процесс будет автоматически завершен при выходе
            )
            
            try:
                # Запускаем сервер
                server_process.start()
                
                # Даем серверу начальное время на запуск
                time.sleep(startup_delay)
                
                # Ожидаем готовности сервера
                if not wait_for_server(HOST, PORT, timeout=max_wait):
                    raise RuntimeError(
                        f"Сервер не запустился в течение {max_wait} секунд. "
                        f"Проверьте конфигурацию и логи."
                    )
                
                print(f"✓ Тестовый сервер запущен на http://{HOST}:{PORT}")
                
                # Выполняем тестовую функцию
                result = test_func(*args, **kwargs)
                
                return result
                
            finally:
                # Останавливаем сервер
                if server_process.is_alive():
                    server_process.terminate()
                    server_process.join(timeout=3)
                    
                    # Если процесс не завершился, принудительно убиваем его
                    if server_process.is_alive():
                        server_process.kill()
                        server_process.join()
                
                print("✓ Тестовый сервер остановлен")
        
        return wrapper
    return decorator