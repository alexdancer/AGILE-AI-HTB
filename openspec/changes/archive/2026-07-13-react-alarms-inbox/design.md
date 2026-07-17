## Context

The Jinja Alarms inbox (`alarms.html` + `alarm_card.html`) is Dismiss-only: every card posts a hidden `action=continue` to `POST /alarms/{id}/resolve`. The backend already supports richer actions — `resolve_alarm` (`db.py:1660`) dispatches to `_apply_alarm_action` for `continue`, `abort_session`, `raise_budget`, and `adjust_guardrail`. Budget alarms (`alarms.py:33` `detect_budget_alarms`) carry the current caps and usage in their own `context` (`daily_cap_tokens`/`daily_used_tokens` for `DAILY_CAP_EXCEEDED`, `session_cap_tokens`/`session_used_tokens` for `SESSION_CAP_EXCEEDED`). `raise_budget` merges its payload into `session.guardrail_overrides.budget`, which is exactly what the overrun check reads back (`task_launch.py:1234-1236`) — so raising a cap on the alarm's session is meaningful and scoped to that session.

Two auth boundaries exist today on `/alarms`: the HTML branch requires `require_portal_auth`, but the JSON branch (`{"alarms": [...]}`) is intentionally open for API polling, and `resolve` only enforces auth for HTML callers. React must not depend on the open JSON route.

This follows the Sessions / Task Breakdown / Task History parity pattern: build-aware canonical GET, a bounded authenticated JSON handoff, a React view in the shared shell, and content-negotiated existing mutations.

## Goals / Non-Goals

**Goals:**
- Serve React for a complete build at canonical `/alarms`, Jinja otherwise.
- New authenticated `GET /api/alarms?filter=open|resolved|all` handoff with bounded projection and per-alarm `available_actions`.
- Backend-computed `available_actions`: `continue` for every open alarm; `raise_budget` (with target cap key + current cap) only for `DAILY_CAP_EXCEEDED`/`SESSION_CAP_EXCEEDED`.
- Backend positive-cap guard in `resolve_alarm` for `raise_budget`.
- React Alarms view: bookmarkable Open/Resolved/All (`?filter=`, default Open), Raise Budget presets (+25%/+50%/+100%) + custom, with confirmation; Resolved rows show action + sanitized payload summary + `resolved_at` + Session Report link.
- Negotiate `POST /alarms/{id}/resolve`: JSON outcome for React, redirect for HTML.

**Non-Goals:**
- No Abort Session in this slice.
- No generic `adjust_guardrail` payload editing in the inbox (link to Guardrail config).
- No change to the legacy open `/alarms` JSON route or its auth.
- No new alarm schema/table/status, no token-accounting change, no Jinja retirement, desktop-only.

## Decisions

- **`available_actions` is derived from alarm type, not React rules.** A backend helper maps each alarm to its allowed actions. Budget cap alarms get a `raise_budget` entry `{action, cap_key, current_cap}` read from the alarm context; all open alarms get `continue`. This keeps eligibility authoritative and lets React render generically. Abort and adjust_guardrail are never emitted.
- **Positive-cap guard lives in `resolve_alarm`.** Before the existing merge, when `action == "raise_budget"`, read the current cap for the payload's cap key from `session.guardrail_overrides.budget` and raise a client error if the new value is not strictly greater. Enforcing it in the domain layer covers both HTML and JSON callers and any future API client — not just the React form.
- **New authed endpoint, legacy untouched.** Add `GET /api/alarms` guarded by `require_portal_auth`, reusing `db.list_alarms` with `resolved` filtering, then project through the bounded helpers already used by other React handoffs (`_bounded_text`, `_bounded_scalar`, `_optional_scalar`, `_safe_local_href`). The existing `/alarms` JSON branch stays exactly as-is for API polling.
- **Resolve negotiation mirrors Task History Unarchive.** Extend `resolve_alarm` route to return a bounded JSON outcome when the caller wants JSON, else keep the 303 redirect. The positive-cap rejection returns a sanitized error outcome envelope (`{ok: false, error}`) for JSON and preserves HTML redirect behavior. The negotiated resolve reuses the shared `/alarms/{id}/resolve` route and its existing auth boundary; only the `GET /api/alarms` data handoff adds Portal auth.
- **Raise Budget UX = presets + custom, computed client-side from `current_cap`.** Presets are +25/50/100% of `current_cap`; custom is a free number. The value submitted is an absolute new cap; the backend guard is the real gate, so client math never needs to be trusted.
- **Filters map to `?filter=` and to `db.list_alarms(resolved=...)`.** `open` → `resolved=False`, `resolved` → `resolved=True`, `all` → no resolved filter. Default Open preserves the existing "resolved stays out of the default inbox" behavior.

## Risks / Trade-offs

- **Content-negotiating `resolve` could regress the HTML redirect.** Mitigation: redirect stays the default branch; JSON only when explicitly requested; test asserts HTML caller still gets 303 to `/alarms`.
- **`current_cap` staleness.** The alarm context snapshots the cap at alarm time; if another action already raised it, the guard reads the live cap from the session overrides (authoritative) and may reject a preset computed from a stale snapshot. Acceptable: the backend is the source of truth and returns a sanitized rejection; React refetches.
- **Payload summary leakage.** Resolved `payload_json` may contain arbitrary keys. Mitigation: sanitize/bound before projecting the resolved payload summary; never echo raw payload.
- **Daily cap raise is per-session.** Raising `daily_cap_tokens` only lifts the alarm's own session gate, not a global daily budget. This is intended HITL scope; document it in the view copy so operators understand the raise is session-scoped.
