from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PROXY_GOVERNED = "proxy_governed"
NATIVE_USAGE = "native_usage"
OBSERVED_ONLY = "observed_only"
LAUNCHABLE_TRACKING_MODES = {PROXY_GOVERNED, NATIVE_USAGE}
TRACKING_MODES = {PROXY_GOVERNED, NATIVE_USAGE, OBSERVED_ONLY}


@dataclass(frozen=True)
class TrackingModePresentation:
    mode: str
    label: str
    runtime_request_guardrails: str
    accounting: str
    budget_authoritative: bool
    launchable_for_board: bool


_TRACKING_MODE_PRESENTATION = {
    PROXY_GOVERNED: TrackingModePresentation(
        mode=PROXY_GOVERNED,
        label="API / Proxy: Governed through Harness Proxy",
        runtime_request_guardrails="Available",
        accounting="Budget-authoritative during run",
        budget_authoritative=True,
        launchable_for_board=True,
    ),
    NATIVE_USAGE: TrackingModePresentation(
        mode=NATIVE_USAGE,
        label="CLI: Track native usage after run",
        runtime_request_guardrails="Not available",
        accounting="Budget-authoritative after run",
        budget_authoritative=True,
        launchable_for_board=True,
    ),
    OBSERVED_ONLY: TrackingModePresentation(
        mode=OBSERVED_ONLY,
        label="CLI: Observe command only",
        runtime_request_guardrails="Not available",
        accounting="Not budget-authoritative",
        budget_authoritative=False,
        launchable_for_board=False,
    ),
}

_UNVERIFIED_PRESENTATION = TrackingModePresentation(
    mode="unverified",
    label="Unverified",
    runtime_request_guardrails="Not available",
    accounting="Not budget-authoritative",
    budget_authoritative=False,
    launchable_for_board=False,
)


def tracking_mode_presentation(mode: str | None) -> TrackingModePresentation:
    return _TRACKING_MODE_PRESENTATION.get(str(mode or ""), _UNVERIFIED_PRESENTATION)


def tracking_mode_view(mode: str | None) -> dict[str, Any]:
    presentation = tracking_mode_presentation(mode)
    return {
        "mode": presentation.mode,
        "label": presentation.label,
        "runtime_request_guardrails": presentation.runtime_request_guardrails,
        "accounting": presentation.accounting,
        "budget_authoritative": presentation.budget_authoritative,
        "launchable_for_board": presentation.launchable_for_board,
    }


def is_budget_authoritative_tracking(evidence: dict[str, Any] | None) -> bool:
    evidence = evidence or {}
    mode = evidence.get("tracking_mode")
    presentation = tracking_mode_presentation(mode)
    # Mode alone is insufficient; verification must explicitly mark the evidence authoritative.
    return presentation.budget_authoritative and bool(evidence.get("tracking_authoritative"))


def is_board_launchable_tracking(evidence: dict[str, Any] | None) -> bool:
    evidence = evidence or {}
    mode = evidence.get("tracking_mode")
    presentation = tracking_mode_presentation(mode)
    return presentation.launchable_for_board and bool(evidence.get("tracking_authoritative"))
