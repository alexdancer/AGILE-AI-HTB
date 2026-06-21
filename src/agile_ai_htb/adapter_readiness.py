from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agile_ai_htb.tracking_modes import (
    OBSERVED_ONLY,
    PROXY_GOVERNED,
    TrackingModePresentation,
    is_board_launchable_tracking,
    is_budget_authoritative_tracking,
    tracking_mode_presentation,
    tracking_mode_view,
)


@dataclass(frozen=True)
class AdapterReadiness:
    adapter: dict[str, Any]
    configured: bool
    verified: bool
    workdir_ready: bool
    models_ready: bool
    selected_model_supported: bool
    tracking: TrackingModePresentation
    tracking_evidence: dict[str, Any]
    budget_authoritative: bool
    launchable_tracking: bool
    ui_launchable: bool
    launchable_for_board: bool
    reasons: list[str]

    def tracking_view(self) -> dict[str, Any]:
        return tracking_mode_view(self.tracking.mode)


def evaluate_adapter_readiness(
    adapter: dict[str, Any],
    *,
    model: str | None = None,
    session_api_key: str | None = None,
    proxy_url: str | None = None,
    include_launch_credentials: bool = False,
) -> AdapterReadiness:
    reasons: list[str] = []
    configured = _is_configured(adapter)
    if not configured:
        reasons.append("Worker adapter is not configured.")

    verified = adapter.get("verification_status") == "verified"
    if not verified:
        reasons.append("Token tracking has not been verified for this adapter.")

    evidence = adapter.get("verification_evidence") or {}
    tracking = tracking_mode_presentation(evidence.get("tracking_mode"))
    budget_authoritative = is_budget_authoritative_tracking(evidence)
    launchable_tracking = is_board_launchable_tracking(evidence)
    if verified:
        if tracking.mode == OBSERVED_ONLY:
            reasons.append("Observed-only Worker tracking cannot launch governed tasks.")
        elif not launchable_tracking:
            reasons.append("Budget-authoritative Worker tracking has not been verified for this adapter.")

    workdir = adapter.get("workdir")
    workdir_ready = bool(workdir) and Path(str(workdir)).is_dir()
    if not workdir:
        reasons.append("Worker adapter workdir is not configured.")
    elif not workdir_ready:
        reasons.append("Worker adapter workdir does not exist.")

    supported_models = adapter.get("supported_models") or []
    models_ready = bool(supported_models)
    selected_model_supported = model is None or bool(supported_models and model in supported_models)
    if not models_ready:
        reasons.append("No discovered Worker models are available for this adapter.")
    elif model is not None and model not in supported_models:
        reasons.append("Selected model is not supported by this adapter.")

    if include_launch_credentials:
        if tracking.mode == PROXY_GOVERNED and not session_api_key:
            reasons.append("Session API key is required for harness proxy token tracking.")
        if tracking.mode == PROXY_GOVERNED and not proxy_url:
            reasons.append("Harness proxy URL is required for adapter launch.")

    ui_launchable = configured and verified and launchable_tracking and models_ready and workdir_ready
    launchable_for_board = ui_launchable and selected_model_supported
    if include_launch_credentials and tracking.mode == PROXY_GOVERNED:
        launchable_for_board = launchable_for_board and bool(session_api_key) and bool(proxy_url)

    return AdapterReadiness(
        adapter=adapter,
        configured=configured,
        verified=verified,
        workdir_ready=workdir_ready,
        models_ready=models_ready,
        selected_model_supported=selected_model_supported,
        tracking=tracking,
        tracking_evidence=evidence,
        budget_authoritative=budget_authoritative,
        launchable_tracking=launchable_tracking,
        ui_launchable=ui_launchable,
        launchable_for_board=launchable_for_board,
        reasons=reasons,
    )


def _is_configured(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    return bool(adapter.get("workdir")) and bool(
        config.get("command")
        or config.get("verification_template")
        or config.get("launch_template")
        or config.get("native_verification_template")
        or config.get("native_launch_template")
    )
