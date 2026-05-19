"""
Проверка «можно ли оценить критерий ИИ»: та же семантика, что фильтрация requirement в пайплайне.
"""

from __future__ import annotations

from src.core.prompts import get_requirement_evaluation_prompt
from src.services.ml_client import ml_generate_non_stream


def can_ai_verify_single_criterion(ml_url: str, criterion_text: str) -> bool:
    """
    True, если локальная LLM считает критерий применимым для объективной ИИ-проверки (YES).
    Совпадает с логикой filter_requirements (LangGraph) и фильтром в Orchestrator.
    """
    raw = ml_generate_non_stream(
        ml_url,
        get_requirement_evaluation_prompt(criterion_text),
        temperature=0.0,
        max_tokens=64,
        timeout=120,
    ).strip()
    verdict = raw.upper().split()
    token = verdict[0] if verdict else ""
    return token == "YES"
