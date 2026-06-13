from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

Severity = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass(frozen=True)
class Alarm:
    id: str
    type: str
    severity: Severity
    session_id: str
    timestamp: str
    context: dict[str, Any]
    recommended_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "context": self.context,
            "recommended_action": self.recommended_action,
        }


def detect_budget_alarms(
    *,
    session_id: str,
    zone: str,
    daily_used_tokens: int,
    daily_cap_tokens: int | None,
    session_used_tokens: int,
    session_cap_tokens: int | None,
    previous_alarms: list[dict[str, Any]],
) -> list[Alarm]:
    alarms: list[Alarm] = []
    previous_types = {alarm.get("type") for alarm in previous_alarms if alarm.get("session_id") == session_id}

    if zone == "yellow" and "BUDGET_YELLOW" not in previous_types:
        alarms.append(
            _alarm(
                "BUDGET_YELLOW",
                "LOW",
                session_id,
                _budget_context(zone, daily_used_tokens, daily_cap_tokens),
                "Agent is in yellow budget zone; concise governance applied.",
            )
        )
    if zone == "red" and "BUDGET_RED" not in previous_types:
        alarms.append(
            _alarm(
                "BUDGET_RED",
                "MEDIUM",
                session_id,
                _budget_context(zone, daily_used_tokens, daily_cap_tokens),
                "Agent is in red budget zone; delivery-only governance applied. Review session.",
            )
        )

    if daily_cap_tokens and daily_used_tokens >= daily_cap_tokens and "DAILY_CAP_EXCEEDED" not in previous_types:
        alarms.append(
            _alarm(
                "DAILY_CAP_EXCEEDED",
                "HIGH",
                session_id,
                {
                    "daily_used_tokens": daily_used_tokens,
                    "daily_cap_tokens": daily_cap_tokens,
                    "daily_remaining_tokens": _remaining(daily_cap_tokens, daily_used_tokens),
                    "daily_usage_ratio": _ratio(daily_used_tokens, daily_cap_tokens),
                },
                "Daily cap exceeded. Human should continue, raise budget, or abort.",
            )
        )

    if session_cap_tokens and session_used_tokens >= session_cap_tokens and "SESSION_CAP_EXCEEDED" not in previous_types:
        alarms.append(
            _alarm(
                "SESSION_CAP_EXCEEDED",
                "MEDIUM",
                session_id,
                {"session_used_tokens": session_used_tokens, "session_cap_tokens": session_cap_tokens},
                "Session cap exceeded. Review session or adjust budget.",
            )
        )

    return alarms


def detect_loop(
    tool_trace: list[dict[str, Any]],
    threshold: int,
    session_id: str = "",
) -> Alarm | None:
    if threshold <= 0:
        return None

    previous_key: tuple[str | None, str | None] | None = None
    count = 0
    for call in tool_trace:
        key = (call.get("tool_name"), call.get("input_hash"))
        if key == previous_key:
            count += 1
        else:
            previous_key = key
            count = 1
        if count >= threshold:
            return _alarm(
                "LOOP_DETECTED",
                "MEDIUM",
                session_id,
                {
                    "tool_name": key[0],
                    "input_hash": key[1],
                    "repetition_count": count,
                },
                "Repeated identical tool call detected. Human should continue, abort, or adjust threshold.",
            )
    return None


def detect_session_timeout(session_id: str, *, elapsed_seconds: int, timeout_seconds: int) -> Alarm | None:
    if elapsed_seconds < timeout_seconds:
        return None
    return _alarm(
        "SESSION_TIMEOUT",
        "MEDIUM",
        session_id,
        {"elapsed_seconds": elapsed_seconds, "timeout_seconds": timeout_seconds},
        "Session timeout exceeded. Save checkpoint and ask human to continue, abort, or extend.",
    )


def detect_tool_category_bias(
    session_id: str,
    *,
    category: str,
    category_token_share: float,
    limit: float,
) -> Alarm | None:
    if category_token_share <= limit:
        return None
    return _alarm(
        "TOOL_CATEGORY_BIAS",
        "LOW",
        session_id,
        {"category": category, "category_token_share": category_token_share, "limit": limit},
        "One tool category dominates session budget. Inject warning context into agent.",
    )


def alarm_for_checkpoint_failure(session_id: str, *, checkpoint_name: str, reason: str) -> Alarm:
    return _alarm(
        "CHECKPOINT_FAIL",
        "MEDIUM",
        session_id,
        {"checkpoint_name": checkpoint_name, "reason": reason},
        "Checkpoint failed. Human review required before advancing task.",
    )


def _alarm(
    alarm_type: str,
    severity: Severity,
    session_id: str,
    context: dict[str, Any],
    recommended_action: str,
) -> Alarm:
    return Alarm(
        id=f"alarm_{uuid.uuid4().hex}",
        type=alarm_type,
        severity=severity,
        session_id=session_id,
        timestamp=datetime.now(UTC).isoformat(),
        context=context,
        recommended_action=recommended_action,
    )


def _budget_context(zone: str, daily_used_tokens: int, daily_cap_tokens: int | None) -> dict[str, Any]:
    return {
        "zone": zone,
        "daily_used_tokens": daily_used_tokens,
        "daily_cap_tokens": daily_cap_tokens,
        "daily_remaining_tokens": _remaining(daily_cap_tokens, daily_used_tokens),
        "daily_usage_ratio": _ratio(daily_used_tokens, daily_cap_tokens),
    }


def _remaining(cap: int | None, used: int) -> int | None:
    if cap is None:
        return None
    return max(cap - used, 0)


def _ratio(used: int, cap: int | None) -> float | None:
    if not cap:
        return None
    return used / cap
