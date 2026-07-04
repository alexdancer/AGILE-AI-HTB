from __future__ import annotations

from pathlib import Path
from typing import Any

from agile_ai_htb import db
from agile_ai_htb.adapter_readiness import evaluate_adapter_readiness
from agile_ai_htb.evidence_reporting import safe_evidence
from agile_ai_htb.tracking_modes import NATIVE_USAGE, OBSERVED_ONLY, PROXY_GOVERNED, tracking_mode_view
from agile_ai_htb.worker_adapters import discovered_worker_model_ids
from agile_ai_htb.worker_model_allowlist import allowed_worker_model_ids


def worker_adapter_view_models(database_path: Path | str) -> list[dict[str, Any]]:
    adapters = []
    for adapter in db.list_worker_adapters(database_path):
        config = adapter.get("config") or {}
        readiness = evaluate_adapter_readiness(adapter)
        tracking = readiness.tracking_view()
        available_tracking_modes = available_worker_tracking_modes(adapter)
        verification_evidence = safe_evidence(adapter.get("verification_evidence") or {})
        verification_diagnostic = verification_evidence.get("diagnostic") if isinstance(verification_evidence, dict) else None
        adapters.append(
            {
                **adapter,
                # Show only operator-approved models as supported; discovered models remain separate setup evidence.
                "supported_models": allowed_worker_model_ids(adapter),
                "verification_evidence": verification_evidence,
                "verification_diagnostic": verification_diagnostic if isinstance(verification_diagnostic, dict) else None,
                "diagnostics": config.get("_diagnostics") or {},
                "launchable": readiness.ui_launchable,
                "discovered_models": discovered_worker_model_ids(adapter),
                "model_discovery": config.get("model_discovery"),
                "model_discovery_label": worker_model_discovery_label(config.get("model_discovery")),
                "tracking_modes": available_tracking_modes,
                "tracking_mode_options": [tracking_mode_view(mode) for mode in available_tracking_modes],
                "connection_type": worker_connection_type(adapter),
                "tracking": tracking,
                "tracking_label": tracking["label"],
            }
        )
    return adapters


def worker_setup_next_action(active_adapter: dict[str, Any] | None, has_projects: bool) -> dict[str, str]:
    # Ordered from earliest setup blocker to launch-ready destination so the UI presents one concrete next step.
    if active_adapter is None:
        return {"label": "Choose active adapter", "href": "/settings/workers", "detail": "No Worker adapter is available."}
    if not active_adapter.get("configured"):
        return {"label": "Choose active adapter", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Mark an adapter as the active default before launch."}
    if not active_adapter.get("discovered_models"):
        return {"label": "Discover models", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Run model discovery so launch controls show approved Worker models."}
    if not active_adapter.get("supported_models"):
        return {"label": "Approve Worker models", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Select at least one discovered model for governed launch."}
    if not active_adapter.get("launchable"):
        diagnostic = active_adapter.get("verification_diagnostic") or {}
        if diagnostic.get("summary"):
            return {
                "label": "Fix CLI setup",
                "href": str(diagnostic.get("setup_href") or f"/settings/workers?adapter_id={active_adapter['id']}"),
                "detail": str(diagnostic["summary"]),
            }
        return {"label": "Verify adapter", "href": f"/settings/workers?adapter_id={active_adapter['id']}", "detail": "Run verification to make this adapter launch-ready."}
    if not has_projects:
        return {"label": "Open local repo", "href": "/projects", "detail": "Connect a project workspace for project-scoped launch."}
    return {"label": "Open task board", "href": "/board", "detail": "Adapter and model selection are launch-ready."}


def worker_model_discovery_label(discovery: dict[str, Any] | None) -> str:
    if not discovery:
        return "not run"
    if discovery.get("tracking_mode") == "curated":
        return "Curated model inventory"
    return "Native model discovery"


def active_adapter_for_request(adapters: list[dict[str, Any]], requested_id: str | None) -> dict[str, Any] | None:
    if requested_id:
        requested = next((adapter for adapter in adapters if adapter["id"] == requested_id), None)
        if requested:
            return requested
    return next(
        (adapter for adapter in adapters if adapter.get("is_default")),
        next((adapter for adapter in adapters if adapter.get("configured")), adapters[0] if adapters else None),
    )


def validate_worker_tracking_mode(database_path: Path | str, adapter_id: str, requested_mode: str) -> None:
    adapter = db.get_worker_adapter(database_path, adapter_id)
    available = available_worker_tracking_modes(adapter)
    if requested_mode not in available:
        raise ValueError(
            f"Tracking mode {requested_mode!r} is not available for this adapter. Available modes: {', '.join(available)}."
        )


def available_worker_tracking_modes(adapter: dict[str, Any]) -> list[str]:
    config = adapter.get("config") or {}
    configured = config.get("tracking_modes")
    proxy_capable = adapter_uses_harness_proxy(adapter)
    native_capable = adapter_can_emit_native_usage(adapter)
    allowed = capability_allowed_tracking_modes(proxy_capable=proxy_capable, native_capable=native_capable)
    if configured:
        modes = [normalize_configured_tracking_mode(mode) for mode in configured]
        # Stored preferences are advisory; hide modes the current adapter cannot actually support.
        modes = [mode for mode in modes if mode in allowed]
        if modes:
            return dedupe_tracking_modes(modes)
    return dedupe_tracking_modes([mode for mode in [PROXY_GOVERNED, NATIVE_USAGE, OBSERVED_ONLY] if mode in allowed])


def capability_allowed_tracking_modes(*, proxy_capable: bool, native_capable: bool) -> set[str]:
    modes: list[str] = []
    if proxy_capable:
        modes.append(PROXY_GOVERNED)
    if native_capable:
        modes.append(NATIVE_USAGE)
    if native_capable or not proxy_capable:
        modes.append(OBSERVED_ONLY)
    return set(modes)


def normalize_configured_tracking_mode(mode: Any) -> str:
    mode = str(mode)
    if mode == "native":
        return NATIVE_USAGE
    return mode


def dedupe_tracking_modes(modes: list[str]) -> list[str]:
    deduped: list[str] = []
    for mode in modes:
        if mode not in deduped:
            deduped.append(mode)
    return deduped


def worker_connection_type(adapter: dict[str, Any]) -> str:
    if adapter_uses_harness_proxy(adapter) and not adapter_can_emit_native_usage(adapter):
        return "API / Proxy Worker"
    if adapter_uses_harness_proxy(adapter):
        return "API / Proxy-capable CLI Worker"
    return "CLI Worker"


def adapter_uses_harness_proxy(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    template = config.get("verification_template") or []
    serialized = " ".join(str(part) for part in template)
    return "{proxy_url}" in serialized and "{session_api_key}" in serialized


def adapter_can_emit_native_usage(adapter: dict[str, Any]) -> bool:
    config = adapter.get("config") or {}
    if config.get("native_verification_template"):
        return True
    return adapter.get("kind") in {"claude_code", "codex", "opencode"}
