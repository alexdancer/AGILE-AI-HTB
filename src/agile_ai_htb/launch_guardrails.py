from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agile_ai_htb import db
from agile_ai_htb.worker_adapters import get_adapter_builder


@dataclass(frozen=True)
class LaunchGuardrailResult:
    passed: bool
    launchable: bool
    reasons: list[str]
    adapter: dict[str, Any] | None = None


def evaluate_launch_guardrails(
    database_path: Path | str,
    *,
    adapter_id: str,
    model: str,
    session_api_key: str | None,
    proxy_url: str | None,
) -> LaunchGuardrailResult:
    try:
        adapter = db.get_worker_adapter(database_path, adapter_id)
    except KeyError:
        return LaunchGuardrailResult(False, False, ["Worker adapter not found."], None)

    reasons: list[str] = []
    if not _is_configured(adapter):
        reasons.append("Worker adapter is not configured.")
    if adapter.get("verification_status") != "verified":
        reasons.append("Token tracking has not been verified for this adapter.")
    workdir = adapter.get("workdir")
    if not workdir:
        reasons.append("Worker adapter workdir is not configured.")
    elif not Path(workdir).is_dir():
        reasons.append("Worker adapter workdir does not exist.")
    if not get_adapter_builder(adapter).supports_model(model):
        reasons.append("Selected model is not supported by this adapter.")
    if not session_api_key:
        reasons.append("Session API key is required for harness proxy token tracking.")
    if not proxy_url:
        reasons.append("Harness proxy URL is required for adapter launch.")

    return LaunchGuardrailResult(not reasons, not reasons, reasons, adapter)


def adapter_launchable_for_ui(adapter: dict[str, Any]) -> bool:
    workdir = adapter.get("workdir")
    return (
        _is_configured(adapter)
        and adapter.get("verification_status") == "verified"
        and bool(workdir)
        and Path(str(workdir)).is_dir()
    )


def _is_configured(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    return bool(adapter.get("workdir")) and bool(
        config.get("command") or config.get("verification_template") or config.get("launch_template")
    )
