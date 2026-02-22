import json
import logging
import requests 
from typing import List, Dict, Any, Optional
from src.core.prompts import (
  get_orchestrator_prompt
)
from src.services.file_processor import FolderStructure

logger = logging.getLogger(__name__)
MOCK_RESPONSE = {
  "text": "smth",
}


class BigBoss:
  def __init__(self, url):
    self.url = url
    self.prompt_cnt = 0

  def _get_answer(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> Dict[str, Any]:
    try:
      self.prompt_cnt += 1
      with open(f'logs/prompt{self.prompt_cnt}', 'w') as f:
        f.write(prompt)
      response = requests.post(
        f'{self.url}/generate',
        json={
          "prompt": prompt,
          "temperature": temperature,
          "stream": False,
          "max_tokens": max_tokens,
        },
        headers={'Content-Type': 'application/json'},
      )
      return response.json()
    except requests.RequestException as e:
      logger.error(f'HTTP request failed {e}.')
      return MOCK_RESPONSE
    
  def audit(self, requirements: Dict[str, int], project: FolderStructure) -> str:
    processed_reqs = ''
    STEP = 3
    for i in range(0, len(requirements.keys()), STEP):
      processed_reqs += self._get_answer(get_orchestrator_prompt(list(requirements.keys())[i:i+STEP]), max_tokens=512)['text']
    return processed_reqs