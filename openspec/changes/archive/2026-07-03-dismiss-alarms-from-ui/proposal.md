## Why

Resolved alarms currently remain on the main Alarms page under "Recently resolved", so operators have no way to completely clear the alarm inbox without losing auditability. We need a UI dismiss path that removes alarm clutter while keeping alarm records and action history intact.

## What Changes

- Add an operator-facing **Dismiss** action for open alarm cards in the Portal.
- Treat Dismiss as acknowledgement/resolution using the existing alarm resolution lifecycle, not archive or delete.
- Hide resolved/dismissed alarms from the default `/alarms` inbox view.
- Preserve resolved alarms in the existing database/API/session evidence path for audit and debugging.
- Keep any resolved-history access secondary instead of a default page section.
- No schema change, no alarm archive state, no hard delete, no SPA rewrite.

## Capabilities

### New Capabilities
- `alarm-inbox`: Portal alarm inbox behavior, including dismissing open alarms from the default UI while preserving audit records.

### Modified Capabilities

## Impact

- Affected Portal routes/templates: `src/agile_ai_htb/routes/alarms.py`, `src/agile_ai_htb/templates/alarms.html`, `src/agile_ai_htb/templates/alarm_card.html`.
- Affected alarm persistence path: existing `db.resolve_alarm` / `action_history` behavior only; no new table or archive metadata.
- Affected tests: Portal alarm UI tests and API alarm resolution/listing tests.
- No dependency, Worker Adapter, token-accounting, or model-layer changes.
