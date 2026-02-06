import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

if __name__ == "__main__":
  uvicorn.run(
    "main:app"
  )
