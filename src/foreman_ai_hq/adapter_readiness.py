from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foreman_ai_hq.tracking_modes import (
    OBSERVED_ONLY,
    PROXY_GOVERNED,
    TrackingModePresentation,
    is_board_launchable_tracking,
    is_budget_authoritative_tracking,
    tracking_mode_presentation,
    tracking_mode_view,
)
from foreman_ai_hq.worker_model_allowlist import allowed_worker_model_ids


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
    read_only_launchable: bool
    read_only_reasons: list[str]
    ui_launchable: bool
    launchable_for_board: bool
    reasons: list[str]

    def tracking_view(self) -> dict[str, Any]:
        return tracking_mode_view(self.tracking.mode)


def evaluate_adapter_readiness(
    adapter: dict[str, Any],
    *,
    model: str | None = None,
    project_root: str | None = None,
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

    workdir = project_root or adapter.get("workdir")
    workdir_ready = not workdir or Path(str(workdir)).is_dir()
    if workdir and not workdir_ready:
        reasons.append("Worker launch project root does not exist.")

    supported_models = allowed_worker_model_ids(adapter)
    models_ready = bool(supported_models)
    selected_model_supported = model is None or bool(supported_models and model in supported_models)
    if not models_ready:
        reasons.append("No allowed Worker models are available for this adapter.")
    elif model is not None and model not in supported_models:
        reasons.append("Selected model is not supported by this adapter.")

    # Launch-time checks include short-lived credentials that should not affect
    # passive UI readiness badges.
    if include_launch_credentials:
        if tracking.mode == PROXY_GOVERNED and not session_api_key:
            reasons.append("Session API key is required for harness proxy token tracking.")
        if tracking.mode == PROXY_GOVERNED and not proxy_url:
            reasons.append("Harness proxy URL is required for adapter launch.")

    ui_launchable = configured and verified and launchable_tracking and models_ready and workdir_ready
    launchable_for_board = ui_launchable and selected_model_supported
    if include_launch_credentials and tracking.mode == PROXY_GOVERNED:
        launchable_for_board = launchable_for_board and bool(session_api_key) and bool(proxy_url)

    read_only_launchable, read_only_reasons = _read_only_launchable(adapter, verified, launchable_tracking)

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
        read_only_launchable=read_only_launchable,
        read_only_reasons=read_only_reasons,
        ui_launchable=ui_launchable,
        launchable_for_board=launchable_for_board,
        reasons=reasons,
    )


def _read_only_launchable(adapter: dict[str, Any], verified: bool, launchable_tracking: bool) -> tuple[bool, list[str]]:
    """Return whether this adapter has a verified adapter-enforced read-only launch profile."""
    reasons: list[str] = []
    if not verified:
        reasons.append("Token tracking has not been verified for this adapter.")
    if verified and not launchable_tracking:
        reasons.append("Budget-authoritative Worker tracking has not been verified for this adapter.")
    kind = str(adapter.get("kind") or "")
    # Only Codex currently ships a verified read-only sandbox profile.
    if kind != "codex":
        reasons.append(f"{kind or 'This'} Worker Adapter does not have a verified read-only launch profile.")
    config = adapter.get("config") or {}
    template = config.get("native_launch_template")
    bypass_flags = ("--full-auto", "--dangerously-bypass-approvals-and-sandbox")
    if kind == "codex" and isinstance(template, list) and any(
        str(part) == flag or str(part).startswith(f"{flag}=")
        for part in template
        for flag in bypass_flags
    ):
        reasons.append("Configured Codex launch flags bypass the verified read-only sandbox.")
    return (not reasons and kind == "codex"), reasons


def _is_configured(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    return bool(
        config.get("command")
        or config.get("verification_template")
        or config.get("launch_template")
        or config.get("native_verification_template")
        or config.get("native_launch_template")
    )
