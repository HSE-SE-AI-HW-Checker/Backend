import json
import logging
import requests 
from typing import List, Dict, Any, Optional
from src.core.prompts import (
  get_orchestrator_prompt,
  get_specialist_prompt,
  get_requirement_evaluation_prompt
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
  def _only_digits(string: str) -> str:
    ans = ''
    for sym in string:
      if '0' <= sym and sym <= '9':
        ans += sym
    return ans

  @staticmethod
  def _increase_indices(string: str, increment: int) -> str:
    try: 
      arr = string.split('\n')
      answer = '  '
      for line in arr:
        parts = line.split(':', 1)
        if len(parts)  == 2:
          parts[0] = str(int(BigBoss._only_digits(parts[0])) + increment)
          answer += f'{parts[0]}: {parts[1]}'
        else:
          answer += line
        answer += '\n  '
      return answer[:-3]
    except Exception as e:
      print(f'Failed to parse string: {string}\nError: {e}')

  def _check_requirements(self, requirements: List[str]) -> List[str]:
    answer = []
    for requirement in requirements:
      model_opinion = self._get_answer(
        get_requirement_evaluation_prompt(requirement),
        max_tokens=64,
        temperature=0
      )['text'].strip()
      if model_opinion == "YES":
         answer.append(requirement)
    return answer

  def audit(self, requirements: Dict[str, int], project: FolderStructure) -> str:
    processed_reqs = ''
    req_list = self._check_requirements(list(requirements.keys()))

    # Словарь для сбора всех назначений: {req_index: role}
    all_assignments = {}

    # Экспериментально подобрал такое значение. С ним работает неплохо
    STEP = 3
    for i in range(0, len(req_list), STEP):
      chunk_reqs = req_list[i:i+STEP]
      last_answer = self._get_answer(get_orchestrator_prompt(
          chunk_reqs
        ), max_tokens=512, temperature=0.1)['text']
      
      # Парсим ответ оркестратора
      parsed_json_str = BigBoss._parse_markdown_answer(last_answer)
      # Убираем запятую в конце, если она есть, для валидного JSON (хотя _parse_markdown_answer добавляет её)
      # Но тут логика была странная: _parse_markdown_answer возвращает строку с запятой в конце.
      # Нам нужно собрать полный JSON из кусочков или парсить кусочки.
      
      # Попробуем распарсить текущий кусок как JSON (с поправкой на формат)
      # _parse_markdown_answer возвращает "key": "value", ...
      # Нам нужно обернуть это в {} чтобы распарсить
      try:
          # Убираем запятую в конце для парсинга
          json_str = f"{{{parsed_json_str.rstrip(',')}}}"
          chunk_assignments = json.loads(json_str)
          
          # Корректируем индексы и сохраняем
          for key, role in chunk_assignments.items():
              # Индексы в ответе оркестратора локальные для чанка (1, 2, 3...) или глобальные?
              # Промпт оркестратора получает список требований. Если он видит их как список, он скорее всего нумерует с 1.
              # В _increase_indices была логика сдвига индексов.
              
              # Воспроизведем логику _increase_indices но для словаря
              try:
                  idx = int(key)
                  global_idx = idx + i # i - смещение
                  all_assignments[global_idx] = role
              except ValueError:
                  logger.warning(f"Skipping invalid key in orchestrator response: {key}")
                  
      except json.JSONDecodeError as e:
          logger.error(f"Failed to parse orchestrator response chunk: {e}")
          # Fallback: если не удалось распарсить, пропускаем этот чанк
          continue

      # Для совместимости со старым возвратом (хотя он нам уже не нужен в таком виде)
      # last_answer_str = BigBoss._increase_indices(parsed_json_str, i)
      # processed_reqs += last_answer_str

    # Теперь у нас есть all_assignments {global_index: role}
    # Запускаем специалистов
    
    specialist_reports = []
    
    # Преобразуем структуру проекта в строку для промпта
    # Используем project.structure, если доступно, иначе строковое представление
    project_structure_str = str(project.structure) if hasattr(project, 'structure') else str(project)
    
    # Собираем контент файлов
    # В FolderStructure ожидается словарь files_content или подобное
    project_files_str = str(project.files_content) if hasattr(project, 'files_content') else "File content not available"

    for idx, role in all_assignments.items():
        # Индекс 1-based в all_assignments (из-за логики +1 в _increase_indices и промпта)
        # Но req_list 0-based.
        # Если global_idx = idx + i, и idx в чанке начинался с 1...
        # В промпте оркестратора: "1": "security".
        # i=0. idx=1. global_idx = 1. req_list[0].
        # Значит req_index = global_idx - 1.
        
        req_index = idx - 1
        if 0 <= req_index < len(req_list):
            requirement_text = req_list[req_index]
            
            logger.info(f"Calling specialist {role} for requirement: {requirement_text[:50]}...")
            
            specialist_prompt = get_specialist_prompt(
                role=role,
                requirement=requirement_text,
                project_structure=project_structure_str,
                project_files=project_files_str
            )
            
            specialist_response = self._get_answer(
                specialist_prompt,
                max_tokens=1024,
                temperature=0.2
            )['text']
            
            report_entry = f"## Requirement {idx} ({role})\n\n{specialist_response}\n"
            specialist_reports.append(report_entry)
        else:
            logger.warning(f"Index {req_index} out of bounds for requirements list")

    final_report = "\n".join(specialist_reports)
    return final_report