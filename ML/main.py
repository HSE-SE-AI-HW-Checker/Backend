from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sys

from server import ServerML

server_instance = ServerML()
app = server_instance.app