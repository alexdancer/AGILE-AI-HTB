## Context

The Control Plane settings page already renders the configured provider/model and a “Test control-plane connection” form. The POST route records sanitized success/failure evidence, but always returns JSON, so a normal browser form submission navigates away from the Portal UI.

The Control Plane model remains separate from Worker Adapter models and credentials. This change only affects how Control Plane connection test results are presented after the test runs.

## Goals / Non-Goals

**Goals:**

- Keep browser operators on the Control Plane settings page after running the test.
- Preserve machine-readable JSON behavior for API clients.
- Show a concise success/failure result in the existing settings UI.
- Keep sanitized raw evidence available without making it the default view.
- Cover success and failure paths with portal tests.

**Non-Goals:**

- No AJAX, SPA, websocket, or new frontend framework.
- No database schema change.
- No new test-status table or route.
- No Worker Adapter setup, launch-readiness, model inventory, or credential changes.
- No change to which LLM request is used for the smoke test.

## Decisions

1. Branch response behavior by request type.
   - Browser/form submissions that accept HTML should record the test result, then return `303 See Other` to `/settings/control-plane`.
   - JSON/API clients should continue receiving the existing `{"passed": ..., "status": ...}` response shape and status codes.
   - Alternative rejected: split browser and API routes. The existing route already represents the action; response negotiation is the smaller change.

2. Reuse the existing execution backend status record.
   - The route already persists `control_plane_model` status with sanitized details.
   - The settings page already reads `connection_status`; it should render a compact summary from that record.
   - Alternative rejected: add flash-session storage. It would duplicate status and disappear on refresh.

3. Render summary first, raw evidence second.
   - Show the operator-facing result as a pill plus provider/model and usage or sanitized error.
   - Put the full sanitized details dictionary under native `<details>` for support/debugging.
   - Alternative rejected: keep the current always-visible `<pre>`. It is accurate but too raw for setup UX.

## Risks / Trade-offs

- [Risk] Test failure currently uses HTTP 503 for JSON clients. → Mitigation: preserve that for API clients, but browser form submissions still redirect after recording failure so the UI can show it cleanly.
- [Risk] Raw evidence may still be useful for support. → Mitigation: keep it in a collapsed native details block, redacted as today.
- [Risk] Accept-header detection can be imperfect. → Mitigation: match existing portal patterns that treat `text/html` without `application/json` as browser intent.
