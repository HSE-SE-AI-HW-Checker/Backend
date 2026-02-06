import uvicorn
import json
import os
import signal
import importlib
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from model import Model

class PromptMessage(BaseModel):
    prompt: str
    is_agent: bool = False

class ServerML: 
    def __init__(self):
        # TODO: read model_name from config
        self.model = Model('gpt2')
        self.app = FastAPI()
        self._setup_handlers()


    def _setup_handlers(self):
        @self.app.post("/ask_ai")
        async def ask_ai(message: PromptMessage):
            return {"message": self.model.responde(message.prompt)}
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}