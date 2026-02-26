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
      with open(f'logs/prompt{self.prompt_cnt}', 'a') as f:
        f.write(f"""
Ответ модели:
{response.json()['text']}
""")
      return response.json()
    except requests.RequestException as e:
      logger.error(f'HTTP request failed {e}.')
      return MOCK_RESPONSE

  @staticmethod
  def _parse_markdown_answer(markdown: str) -> str:
    return markdown[markdown.find('{') + 1: markdown.find('}') - 1] + ','

  @staticmethod
  def _increase_indices(string: str, increment: int) -> str:
    arr = string.split('\n')
    answer = '  '
    for line in arr:
      parts = line.split(':', 1)
      if len(parts)  == 2:
        parts[0] = str(int(parts[0][parts[0].find('"') + 1: -1]) + increment)
        answer += f'{parts[0]}: {parts[1]}'
      else:
        answer += line
      answer += '\n  '
    return answer[:-3]

  def audit(self, requirements: Dict[str, int], project: FolderStructure) -> str:
    processed_reqs = ''

    # Экспериментально подобрал такое значение. С ним работает неплохо
    STEP = 3
    for i in range(0, len(requirements.keys()), STEP):
      last_answer = self._get_answer(get_orchestrator_prompt(
          list(requirements.keys())[i:i+STEP]
        ), max_tokens=512, temperature=0.1)['text']
      last_answer = BigBoss._parse_markdown_answer(
        last_answer
      )
      last_answer = BigBoss._increase_indices(last_answer, i)
      processed_reqs += last_answer

    return f'{{{processed_reqs}\n}}'