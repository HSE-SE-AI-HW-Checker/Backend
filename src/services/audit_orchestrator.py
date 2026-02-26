import json
import logging
import requests
from typing import List, Dict, Any, Optional
from src.core.prompts import (
    get_classification_prompt,
    get_role_based_prompt,
    get_aggregation_prompt,
    get_audit_prompt
)

logger = logging.getLogger(__name__)

class AuditOrchestrator:
    """
    Оркестратор процесса аудита кода.
    Управляет классификацией требований, выполнением проверок по ролям и агрегацией результатов.
    """

    def __init__(self, ml_service_url: str):
        self.ml_service_url = ml_service_url

    def _call_ml_service(self, prompt: str, temperature: float = 0.2) -> str:
        """Выполняет запрос к ML сервису."""
        try:
            with open('logs/last_prompt.txt', 'a') as f:
                f.write(prompt)
            response = requests.post(
                f"{self.ml_service_url}/generate",
                json={"prompt": prompt, "temperature": temperature, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("text", "")
        except requests.RequestException as e:
            logger.error(f"ML Service call failed: {e}")
            raise

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Пытается распарсить JSON из ответа модели."""
        try:
            # Попытка найти JSON блок, если модель добавила лишний текст
            with open('logs/last_json.txt', 'w') as f:
                f.write(response_text)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                return json.loads(json_str)
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}. Response: {response_text[:200]}...")
            raise

    def classify_requirements(self, requirements: List[str]) -> Dict[str, str]:
        """
        Классифицирует требования по ролям.
        Returns:
            Dict[req_id, role_name]
        """
        # Формируем список требований с ID для промпта
        req_text = "\n".join([f"{i+1}. {req}" for i, req in enumerate(requirements)])
        prompt = get_classification_prompt(req_text)
        
        response = self._call_ml_service(prompt, temperature=0.1)
        with open("logs/classification_response.txt", 'w') as f:
            f.write(response)
        try:
            mapping = self._parse_json_response(response)
            # Приводим ключи к строкам для единообразия
            return {str(k): v for k, v in mapping.items()}
        except Exception as e:
            logger.warning(f"Classification failed: {e}. Falling back to 'functional' role for all.")
            return {str(i+1): "functional" for i in range(len(requirements))}

    def evaluate_requirement(self, role: str, requirement: str, project_structure: str, project_files: str) -> Dict[str, Any]:
        """Оценивает одно требование с использованием специализированной роли."""
        prompt = get_role_based_prompt(role, requirement, project_structure, project_files)
        response = self._call_ml_service(prompt, temperature=0.2)
        return self._parse_json_response(response)

    def aggregate_results(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Агрегирует результаты проверок."""
        # Сначала попробуем простую математическую агрегацию
        total_score = 0
        count = 0
        for eval_item in evaluations:
            score = eval_item.get("score")
            if score is not None:
                total_score += float(score)
                count += 1
        
        avg_score = round(total_score / count, 2) if count > 0 else 0

        # Генерируем текстовое резюме через модель
        evals_json = json.dumps(evaluations, ensure_ascii=False, indent=2)
        prompt = get_aggregation_prompt(evals_json)
        
        try:
            response = self._call_ml_service(prompt, temperature=0.3)
            summary_data = self._parse_json_response(response)
            final_feedback = summary_data.get("general_feedback", "Аудит завершен.")
            # Модель может скорректировать балл, но лучше доверять математике или взять среднее
            # model_score = summary_data.get("total_score", avg_score)
        except Exception:
            logger.warning("Aggregation prompt failed, using calculated average.")
            final_feedback = "Автоматическая агрегация результатов."
        
        return {
            "evaluations": evaluations,
            "total_score": avg_score,
            "general_feedback": final_feedback
        }

    def run_audit(self, requirements: List[str], project_structure: str, project_files: str) -> Dict[str, Any]:
        """
        Основной метод запуска многоэтапного аудита.
        """
        logger.info("Starting multi-prompt audit...")
        
        # 1. Классификация
        role_mapping = self.classify_requirements(requirements)
        logger.info(f"Requirements classified: {role_mapping}")
        with open("logs/classified_requirements.txt", 'w') as f:
            f.write('\n'.join([f'{key} {value}' for (key, value) in role_mapping.items()]))

        evaluations = []

        # 2. Выполнение проверок (последовательно)
        for i, req_text in enumerate(requirements):
            req_id = str(i + 1)
            role = role_mapping.get(req_id, "functional")
            
            logger.info(f"Evaluating req {req_id} ({role})...")
            try:
                result = self.evaluate_requirement(role, req_text, project_structure, project_files)
                
                # Добавляем метаданные к результату
                result["requirement_id"] = i + 1
                result["requirement_text"] = req_text
                result["role"] = role
                
                evaluations.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate req {req_id}: {e}")
                # Добавляем заглушку при ошибке
                evaluations.append({
                    "requirement_id": i + 1,
                    "requirement_text": req_text,
                    "score": 0,
                    "justification": f"Ошибка при анализе: {str(e)}",
                    "suggestions": "Повторите проверку."
                })

        # 3. Агрегация
        final_report = self.aggregate_results(evaluations)
        return final_report

    def run_legacy_audit(self, requirements: List[str], project_structure: str, project_files: str) -> Dict[str, Any]:
        """Fallback метод: старый монолитный промпт."""
        logger.info("Running legacy audit fallback...")
        req_str = "\n".join(requirements)
        prompt = get_audit_prompt(req_str, project_structure, project_files)
        
        response = self._call_ml_service(prompt)
        return self._parse_json_response(response)