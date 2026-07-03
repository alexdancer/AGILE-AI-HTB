## Why

Operators need a way to restart the current day's launch budget counter after intentional setup, testing, or demo spend without destroying the token ledger evidence that proves what the Harness and Workers actually used. The current daily budget window is tied only to local midnight, so a bad or noisy run can make the rest of the day look budget-exhausted even when the operator wants to continue with a fresh guardrail window.

## What Changes

- Add a Token budget page action labeled as a soft reset, such as **Reset today's budget counter** or **Start new daily budget window**.
- Persist a reset timestamp in portal budget settings instead of deleting or rewriting token ledger rows.
- Calculate daily governed budget usage, budget zone, launch remaining capacity, and budget alarms from the later of local-day start and the latest reset timestamp.
- Show the active budget window start and explain that reset preserves token ledger rows, session reports, task `actual_tokens`, raw provider evidence, and historical audit views.
- Keep per-session Worker caps and task actuals unchanged and Worker-only.
- Do not add a hard delete/reset path for token usage evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `token-budget-setup`: add soft reset semantics for the daily governed budget counter while preserving token ledger evidence and Worker task actuals.

## Impact

- Portal Token budget settings UI and authenticated POST handling.
- Token budget settings persistence in the existing portal settings store.
- Shared daily budget window calculation used by dashboard budget display, launch preflight remaining-capacity checks, proxy/budget alarm calculations, and related tests.
- No Worker Adapter, Control Plane model, provider auth, token ledger deletion, or schema-table rewrite is intended.
