from __future__ import annotations

from typing import Any


SEEDED_WORKER_ADAPTER_MODELS = {
    "claude_code": [
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
    ],
    "codex": ["gpt-5.1-codex", "openai/gpt-4.1-mini"],
    "opencode": ["opencode/gpt-5.1", "gpt-5.1-codex"],
    "hermes": ["anthropic/claude-sonnet-4", "openai/gpt-5.1"],
}

LEGACY_SEEDED_WORKER_ADAPTER_MODEL_SETS = {
    "claude_code": [
        ["claude-3-5-sonnet-latest", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"],
    ],
}


def allowed_worker_model_ids(adapter: dict[str, Any]) -> list[str]:
    config = adapter.get("config") or {}
    models = [str(model) for model in adapter.get("supported_models") or []]
    if not config.get("allowed_models_configured") and _models_match_unapproved_seeded_default(str(adapter.get("id")), models):
        return []
    return models


def _models_match_unapproved_seeded_default(adapter_id: str, models: list[str]) -> bool:
    seeded_model_sets = [SEEDED_WORKER_ADAPTER_MODELS.get(adapter_id) or []]
    seeded_model_sets.extend(LEGACY_SEEDED_WORKER_ADAPTER_MODEL_SETS.get(adapter_id, []))
    return any(models == seeded_models for seeded_models in seeded_model_sets if seeded_models)
