from __future__ import annotations

from typing import Any


SEEDED_WORKER_ADAPTER_MODELS = {
    "claude_code": ["claude-3-5-sonnet-latest", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"],
    "codex": ["gpt-5.1-codex", "openai/gpt-4.1-mini"],
    "opencode": ["opencode/gpt-5.1", "gpt-5.1-codex"],
    "hermes": ["anthropic/claude-sonnet-4", "openai/gpt-5.1"],
}


def allowed_worker_model_ids(adapter: dict[str, Any]) -> list[str]:
    config = adapter.get("config") or {}
    models = [str(model) for model in adapter.get("supported_models") or []]
    seeded_models = SEEDED_WORKER_ADAPTER_MODELS.get(str(adapter.get("id")))
    if not config.get("allowed_models_configured") and seeded_models and models == seeded_models:
        return []
    return models
