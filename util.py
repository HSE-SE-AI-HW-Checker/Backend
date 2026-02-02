import importlib
import json

def get_implementation(module_name, class_name):
    return getattr(importlib.import_module(module_name), class_name)

def available_implementations(module_name):
    ans = []
    for elem in getattr(importlib.import_module(module_name), 'Logger').__subclasses__():
        ans.append(elem.__name__)
    return ans

def get_from_config(key, config='configs/default_config.json'):
    with open(config, 'r') as f:
        return json.load(f)[key]
    
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