import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import importlib
import json

class BackendPath:
    def __init__(self, path_from_root=''):
        """
            path_from_root - путь к файлу относительно Backend/
        """
        self.path = os.path.join(BackendPath._get_root_path(), path_from_root)

    @staticmethod
    def _get_root_path():
        return os.path.dirname(os.path.abspath(__file__))

    def __str__(self):
        return self.path
    
    def __repr__(self):
        return f"BackendPath('{self.path}')"
    
    def __fspath__(self):
        """Поддержка протокола os.PathLike для использования с open(), os.path и т.д."""
        return self.path
    
    def __truediv__(self, other):
        """Поддержка оператора / для создания путей"""
        return BackendPath(os.path.join(self.path, str(other)))
    
    def __add__(self, other):
        """Поддержка конкатенации со строками"""
        return str(self.path) + str(other)
    
    def __radd__(self, other):
        """Поддержка конкатенации со строками слева"""
        return str(other) + str(self.path)


class MLPath(BackendPath):
    def __init__(self, path_from_root=''):
        super().__init__(os.path.join('ML', path_from_root))

def get_implementation(module_name, class_name):
    return getattr(importlib.import_module(module_name), class_name)

def available_implementations(module_name):
    ans = []
    for elem in getattr(importlib.import_module(module_name), 'Logger').__subclasses__():
        ans.append(elem.__name__)
    return ans

def get_from_config(key, config='default_config.json'):
    config_path = os.path.join(str(BackendPath()), 'configs', config)
    with open(config_path, 'r') as f:
        return json.load(f)[key]

def get_url_from_config(config='default_config.json'):
    return f'http://{get_from_config("host", config)}:{get_from_config("port", config)}'

def parse_args(args):
    ans = {}
    for arg in args:
        if '=' not in arg:
            ans[arg] = True
        key, value = arg.split('=')
        ans[key] = value
    return ans

def parse_submittion(submittion):
    # Ссылка на git подобную штуку
    if submittion.data_type == 0:
        pass
    # Архив 
    elif submittion.data_type == 1:
        pass
    # Формат с окошком на каждый файл (обсуждали в личке)
    elif submittion.data_type == 2:
        pass
    else:
        return 