import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import uvicorn
import yaml
from util import MLPath

if __name__ == "__main__":

  with open(MLPath("configs/gpt2_config.yaml"), "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)
    with open(MLPath("configs/active_config.yaml"), "w") as out:
      out.write(yaml.dump(config))

  sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  uvicorn.run(
    "main_ml:app"
  )
