# Implementation Plan: Multi-Prompt Audit System

## Overview
Transition from a monolithic single-prompt audit to a multi-stage process:
1.  **Classification**: Analyze requirements to assign specific audit roles.
2.  **Execution**: Sequentially process requirements using specialized prompts.
3.  **Aggregation**: Combine results into a final report.

## Phase 1: Prompt Engineering (`src/core/prompts.py`)

We will decompose `get_audit_prompt` into a system of prompts.

### 1.1 Classification Prompt
*   **Goal**: Map each requirement to a specific audit role.
*   **Input**: List of requirements.
*   **Output**: JSON mapping `{ "req_id": "role_name" }`.
*   **Roles**:
    *   `security`: Vulnerabilities, auth, data protection.
    *   `performance`: Complexity, resource usage, optimization.
    *   `maintainability`: Code style, patterns, clean code.
    *   `functional`: Logic correctness, edge cases.
    *   `architecture`: Structure, dependencies, modularity.

### 1.2 Specialized Prompts
Each role will have a dedicated system prompt focusing the model's attention.
*   **Structure**:
    *   `System`: "You are an expert [Role Name]..."
    *   `Context`: Project structure and file contents (Cached Prefix).
    *   `Task`: Specific requirement to verify.
    *   `Output Format`: Strict JSON.

## Phase 2: ML Service Optimization (`ML/`)

Since memory is not limited, we will leverage **KV Cache** (Context Caching) inherent in LLMs to speed up sequential requests sharing the same project context.

### 2.1 Context Management
*   Ensure the "Project Context" (file dumps) is placed at the *beginning* of the prompt and remains byte-for-byte identical across requests.
*   The variable parts (specific requirement instructions) will be appended at the end.
*   This allows the ML engine to reuse the processed tokens for the project files.

## Phase 3: Orchestration Logic (`src/services/`)

We will introduce a new flow in `FileProcessor` or a dedicated `AuditOrchestrator`.

### 3.1 Workflow
1.  **Prepare Context**: Generate the static project context string once.
2.  **Router Step**:
    *   Send requirements to ML.
    *   Parse JSON response.
    *   *Fallback*: If parsing fails, revert to legacy single-prompt mode.
3.  **Execution Loop**:
    *   Group requirements by Role (to potentially batch them, or just keep logical consistency).
    *   For each requirement (or small batch):
        *   Construct prompt: `[Static Context] + [Role Instruction] + [Requirement]`.
        *   Call ML API.
        *   Validate and store result.
4.  **Aggregation**:
    *   Merge all partial evaluations.
    *   Calculate total score.
    *   Generate final summary.

## Phase 4: Integration & Fallback

*   **Config**: Add flags to `config.yaml` to enable/disable multi-prompt mode.
*   **Fallback**: Wrap the new logic in a `try-except` block. On any critical failure (JSON parse error, API timeout), log the error and call the legacy `get_audit_prompt` flow.

## Step-by-Step Implementation Tasks

1.  [ ] **Prompts**: Create `src/core/prompts_v2.py` (or extend existing) with `get_classifier_prompt` and `get_role_prompt`.
2.  [ ] **ML API**: Verify `ML/api_server.py` handles requests correctly. (No major changes needed if we rely on implicit caching, but we might want to add a `system_prompt` field if not present).
3.  [ ] **Orchestrator**: Create `src/services/audit_orchestrator.py` to encapsulate the multi-step logic.
4.  [ ] **Integration**: Update `src/services/file_processor.py` to use `AuditOrchestrator`.
5.  [ ] **Testing**: Verify fallback works and quality improves.