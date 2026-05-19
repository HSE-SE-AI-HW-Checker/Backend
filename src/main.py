"""
Точка входа для Backend приложения.
"""

import sys

from .core.server import Server

server_instance = Server(sys.argv[1:])
app = server_instance.app
