import importlib

def get_implementation(module_name, class_name):
    return getattr(importlib.import_module(module_name), class_name)

def available_implementations(module_name):
    ans = []
    for elem in getattr(importlib.import_module(module_name), 'Logger').__subclasses__():
        ans.append(elem.__name__)
    return ans