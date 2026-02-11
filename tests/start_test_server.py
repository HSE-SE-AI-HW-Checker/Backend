import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from src.core.config_manager import get_from_config

if __name__ == "__main__":

  CONFIG = 'testing'
  sys.argv = ['', f'config={CONFIG}']

  HOST = get_from_config('host', CONFIG)
  PORT = get_from_config('port', CONFIG)
  RELOAD = get_from_config('reload', CONFIG)

  uvicorn.run(
    "src.main:app",
    host=HOST,
    port=PORT,
    reload=RELOAD
  )
