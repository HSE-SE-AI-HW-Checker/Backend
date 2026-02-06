from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server_ml import ServerML

server_instance = ServerML('active_config.yaml')
app = server_instance.app

if __name__ == "__main__":
    server_instance.run()