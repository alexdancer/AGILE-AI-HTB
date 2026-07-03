## Context

The current Alarms route already separates open and resolved alarms by `resolved_at`, and the API already supports `resolved=true/false` filtering. The Portal still renders a default "Recently resolved" section, so resolved alarms remain visible clutter even after the operator resolves them.

Alarm dismissal should mean acknowledgement/resolution, not task-style archive. Alarms are governance/audit events tied to sessions; deleting or archiving them would weaken audit evidence and add a second lifecycle flag for the same UI problem.

## Goals / Non-Goals

**Goals:**

- Let operators clear an open alarm from the default Alarms UI with one **Dismiss** action.
- Reuse the existing `resolved_at` + `action_history` alarm resolution path.
- Keep resolved alarm records available through existing API/session evidence paths.
- Keep the default Alarms page focused on active/open alarms.

**Non-Goals:**

- No alarm archive state or `archived_at` metadata.
- No hard delete or data retention change.
- No database schema migration.
- No new workflow state beyond open/resolved.
- No SPA, websocket, notification, or bulk dismissal work.

## Decisions

- **Dismiss maps to existing resolution.** The UI can submit `action=continue` to `/alarms/{alarm_id}/resolve`, which sets `resolved_at` and records action history.
  - Alternative: add a new `dismiss` action. Rejected because it adds API vocabulary without new persistence behavior.
  - Alternative: add `dismissed_at`. Rejected because it duplicates `resolved_at` and creates confusing states like resolved-but-not-dismissed.

- **Default inbox shows open alarms only.** `/alarms` HTML should prioritize unresolved alarms and not render resolved alarms as a default section.
  - Alternative: keep "Recently resolved" under the inbox. Rejected because the user's goal is to completely clear dismissed alarms from the UI.
  - Alternative: delete resolved alarms. Rejected because audit evidence should stay intact.

- **Resolved history stays secondary.** API filtering already exposes `?resolved=true`; implementation may add a small secondary link or filtered view later, but not a main-page resolved list.
  - Alternative: build a separate history page now. Rejected as more UI than needed for the first slice.

## Risks / Trade-offs

- **Risk: Operators think Dismiss deletes the alarm.** → Mitigation: tests and copy should preserve resolved/audit semantics; avoid archive/delete wording.
- **Risk: Resolved alarms become harder to find in the Portal.** → Mitigation: keep API/session evidence unchanged; add only a small secondary history affordance if implementation needs visible audit access.
- **Risk: Form submissions need HTML-friendly response handling.** → Mitigation: reuse existing resolve route or add minimal HTML redirect behavior while preserving JSON responses for API clients.
