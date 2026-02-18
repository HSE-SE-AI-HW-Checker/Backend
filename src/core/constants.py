"""
Константы проекта.
"""

DEFAULT_MOCK_RESPONSE = """
{
  "evaluations": [
    {
      "requirement_id": 1,
      "requirement_text": "Использование паттернов проектирования...",
      "score": 5,
      "max_score": 10,
      "justification": "Обнаружен паттерн Singleton в файле src/db.py (класс Database). Паттерн Factory в src/utils.py реализован с ошибкой (нарушен принцип OCP).",
      "suggestions": "Рекомендуется исправить реализацию Factory, используя абстрактный базовый класс."
    }
  ],
  "total_score": 5,
  "general_feedback": "Проект имеет хорошую структуру, но требует доработки в части архитектурных паттернов."
}
"""