# estimator-project-context Specification

## Purpose

Define how project-scoped estimation incorporates bounded repository context while preserving no-context estimation behavior.

## Requirements

### Requirement: Estimator receives project context when available

When a task is estimated from a project board, the estimator LLM SHALL receive a compact project context brief produced by `build_repo_context_brief()` containing the project's manifests, file tree sample, detected test commands, entry points, and repo-level instruction document excerpts (redacted for secrets).

The context brief SHALL be capped at 8,000 characters.

When no connected project exists (global board estimation), the estimator SHALL receive only the task description and budget numbers with no project context — preserving existing behavior for non-project estimation flows.

#### Scenario: Project-context estimation

- **WHEN** an operator enters a task on a project board (`/projects/{id}/board`) and requests estimation
- **THEN** the estimator LLM call includes a `project_context` field containing the rendered repo context brief text
- **AND** the system prompt includes structural project facts (manifests, test commands, entry points)

#### Scenario: Global board estimation without project context

- **WHEN** an operator enters a task on the global board with no connected project
- **THEN** the estimator LLM call receives no `project_context` field
- **AND** estimation proceeds with the existing task-description-only prompt

#### Scenario: Project context includes test commands

- **WHEN** a project has `pyproject.toml` in its manifests
- **THEN** the context brief SHALL include `pytest` as a detected test command

#### Scenario: Project context redacts secrets

- **WHEN** the project root contains `.env` or other secret-named files
- **THEN** those files SHALL be omitted from the context brief
- **AND** secret patterns (API keys, tokens) in included documents SHALL be replaced with `***REDACTED***`

### Requirement: Estimator preserves existing behavior when no project context is available

The estimator function `estimate_task()` SHALL accept an optional `project_root` parameter. When `project_root` is None or omitted, the estimator SHALL produce estimates using only the task description and budget numbers — identical to current behavior.

#### Scenario: Estimator called without project root

- **WHEN** `estimate_task()` is called with `project_root=None`
- **THEN** the LLM call uses the existing prompt structure with no project context
- **AND** the function signature is backward-compatible

#### Scenario: Estimator called with invalid project root

- **WHEN** `estimate_task()` is called with a `project_root` that does not exist on disk
- **THEN** the estimator SHALL fall back to no-context estimation
- **AND** the call SHALL NOT raise an exception
