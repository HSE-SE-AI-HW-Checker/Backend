import json
import logging
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from src.core.prompts import (
    get_orchestrator_prompt,
    get_specialist_prompt,
)
from src.services.criterion_ai_gate import can_ai_verify_single_criterion
from src.services.file_processor import FolderStructure
from src.services.ml_client import ml_generate_non_stream

logger = logging.getLogger(__name__)

ALLOWED_ROLES = {"security", "performance", "maintainability", "functional", "architecture"}


class AuditState(TypedDict):
    requirements: List[str]
    filtered_requirements: List[str]
    assignments: Dict[int, str]
    specialist_reports: List[str]
    project_structure: str
    project_files: str
    errors: List[str]


class LangGraphOrchestrator:
    """
    Реализация агента аудита на LangGraph.
    """

    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self.graph = self._build_graph()

    def _call_model(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> str:
        return ml_generate_non_stream(
            self.url,
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=120,
        )

    @staticmethod
    def _extract_json_block(text: str) -> Dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("JSON block not found in model response")
        return json.loads(text[start : end + 1])

    def _filter_requirements_node(self, state: AuditState) -> AuditState:
        filtered: List[str] = []
        errors = list(state["errors"])

        for requirement in state["requirements"]:
            try:
                if can_ai_verify_single_criterion(self.url, requirement):
                    filtered.append(requirement)
            except Exception as exc:
                errors.append(f"Filter failed for requirement '{requirement[:40]}': {exc}")

        return {**state, "filtered_requirements": filtered, "errors": errors}

    def _orchestrate_node(self, state: AuditState) -> AuditState:
        requirements = state["filtered_requirements"]
        if not requirements:
            return {**state, "assignments": {}}

        try:
            raw = self._call_model(get_orchestrator_prompt(requirements), temperature=0.1, max_tokens=512)
            mapping = self._extract_json_block(raw)
            assignments: Dict[int, str] = {}
            for key, value in mapping.items():
                idx = int(str(key))
                role = str(value).strip().lower()
                assignments[idx] = role if role in ALLOWED_ROLES else "functional"
            return {**state, "assignments": assignments}
        except Exception as exc:
            fallback = {i + 1: "functional" for i in range(len(requirements))}
            return {**state, "assignments": fallback, "errors": [*state["errors"], f"Orchestration failed: {exc}"]}

    def _run_specialists_node(self, state: AuditState) -> AuditState:
        reports: List[str] = []
        requirements = state["filtered_requirements"]

        for idx, role in sorted(state["assignments"].items(), key=lambda x: x[0]):
            req_idx = idx - 1
            if req_idx < 0 or req_idx >= len(requirements):
                continue

            requirement = requirements[req_idx]
            try:
                specialist_prompt = get_specialist_prompt(
                    role=role,
                    requirement=requirement,
                    project_structure=state["project_structure"],
                    project_files=state["project_files"],
                )
                result = self._call_model(specialist_prompt, temperature=0.2, max_tokens=1024)
                reports.append(f"## Requirement {idx} ({role})\n\n{result}\n")
            except Exception as exc:
                reports.append(
                    f"## Requirement {idx} ({role})\n\n"
                    f'{{"score": 0, "max_score": 10, "justification": "Ошибка анализа: {exc}", "suggestions": "Повторите запрос"}}\n'
                )

        return {**state, "specialist_reports": reports}

    def _build_graph(self):
        graph = StateGraph(AuditState)
        graph.add_node("filter_requirements", self._filter_requirements_node)
        graph.add_node("orchestrate", self._orchestrate_node)
        graph.add_node("run_specialists", self._run_specialists_node)

        graph.add_edge(START, "filter_requirements")
        graph.add_edge("filter_requirements", "orchestrate")
        graph.add_edge("orchestrate", "run_specialists")
        graph.add_edge("run_specialists", END)

        return graph.compile()

    @staticmethod
    def _project_structure(project: FolderStructure) -> str:
        return str(project)

    @staticmethod
    def _project_files(project: FolderStructure) -> str:
        if hasattr(project, "get_files_content"):
            try:
                return project.get_files_content() or ""
            except Exception:
                return ""
        return str(getattr(project, "file_contents", {}))

    def audit(self, requirements: Dict[str, int], project: FolderStructure) -> str:
        initial_state: AuditState = {
            "requirements": list(requirements.keys()),
            "filtered_requirements": [],
            "assignments": {},
            "specialist_reports": [],
            "project_structure": self._project_structure(project),
            "project_files": self._project_files(project),
            "errors": [],
        }
        final_state = self.graph.invoke(initial_state)
        if final_state["errors"]:
            logger.warning("LangGraph audit completed with errors: %s", "; ".join(final_state["errors"]))
        return "\n".join(final_state["specialist_reports"])
