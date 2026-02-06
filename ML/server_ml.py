import uvicorn
import os
import sys
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Model
from util import MLPath

DEFAULT_CONFIG_SETTINGS = {
    'server': {'host': '0.0.0.0', 'port': 8000},
    'model': {'name': 'gpt2'}
}

class PromptMessage(BaseModel):
    prompt: str
    is_agent: bool = False

class ServerML:
    def __init__(self, config_path='gpt2_config.yaml'):
        # Загрузка конфигурации
        self.config = self._load_config(config_path)
        
        # Инициализация модели с параметром из конфига
        model_name = self.config.get('model', {}).get('name', 'gpt2')
        self.model = Model(model_name)
        
        # Инициализация FastAPI
        self.app = FastAPI()
        self._setup_handlers()
    
    def _load_config(self, config):
        """Загружает конфигурацию из YAML файла"""
        config_path = MLPath(f'configs/{config}')
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Конфигурационный файл {config_path} не найден. Используются значения по умолчанию.")
            return DEFAULT_CONFIG_SETTINGS
        except yaml.YAMLError as e:
            print(f"Ошибка при чтении конфигурационного файла: {e}. Используются значения по умолчанию.")
            return DEFAULT_CONFIG_SETTINGS
    
    def run(self):
        """Запускает сервер с параметрами из конфигурации"""
        host = self.config.get('server', {}).get('host', '0.0.0.0')
        port = self.config.get('server', {}).get('port', 8000)
        
        print(f"Запуск сервера на {host}:{port}")
        print(f"Используется модель: {self.config.get('model', {}).get('name', 'gpt2')}")
        
        uvicorn.run(self.app, host=host, port=port)


    def _setup_handlers(self):
        @self.app.post("/ask_ai")
        async def ask_ai(message: PromptMessage):
            return {"message": self.model.responde(message.prompt)}
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}