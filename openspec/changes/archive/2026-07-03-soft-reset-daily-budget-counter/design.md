## Context

Daily token budget usage currently derives from token ledger rows since the local day's midnight boundary. That is correct for ordinary daily governance, but it gives the operator no safe way to recover from intentional setup/demo/test spend during the same day. The token ledger is also audit evidence for Worker Runs, control-plane orchestration, Agent Review/reporting, adapter verification, session reports, and task actuals, so resetting must not mutate or delete token rows.

The agreed behavior is a soft reset: move the daily budget counter's effective window start forward while preserving historical evidence. Daily budget semantics stay based on normalized governed model spend, while per-session Worker caps and task `actual_tokens` remain Worker-execution scoped.

## Goals / Non-Goals

**Goals:**

- Provide an explicit operator action on the Token budget page to reset today's daily governed budget counter.
- Persist the reset as a timestamp/waterline in existing budget settings or equivalent portal state.
- Use one shared effective budget window helper for daily dashboard usage, launch preflight remaining capacity, proxy governance/alarm calculations, and budget-page display.
- Preserve token ledger rows, session reports, raw provider evidence, task `actual_tokens`, and historical audit views.
- Make UI copy unambiguous that this is a soft reset of the guardrail counter, not evidence deletion.

**Non-Goals:**

- No deletion, truncation, or mutation of `token_turns` or session artifacts.
- No change to Worker Adapter tracking modes, native/proxy/observed authority, or provider authentication.
- No change to per-session Worker cap semantics.
- No change to task `actual_tokens` or estimation accuracy calculations.
- No portal rewrite or new frontend framework.
- No automatic scheduled resets beyond the existing local-day boundary.

## Decisions

### Store a reset waterline instead of editing ledger rows

Persist `daily_usage_reset_at` in the existing token budget settings state. The active daily budget window starts at `max(local_day_start, daily_usage_reset_at)` when a reset exists for the current day.

Alternative considered: delete or mark old token rows as reset. Rejected because it breaks auditability and can make session reports, Worker Run evidence, and budget analytics disagree.

### Centralize effective budget window calculation

Introduce or reuse a single helper that returns the current daily budget window start. All daily-budget consumers should use this helper instead of independently calling local midnight logic.

Consumers include:

- Dashboard daily governed budget usage and zone.
- Token budget page current-window usage display.
- Launch preflight remaining capacity and budget override metadata.
- Proxy daily-used and budget alarm calculations.
- Tests or reports that intentionally assert current daily budget behavior.

Alternative considered: apply reset only in the Token budget page. Rejected because UI would say the counter reset while launches and alarms still use midnight usage.

### Preserve historical reporting while clarifying current-window reporting

The budget page should show the active window start and the current-window governed spend. Existing session reports and historical token evidence continue to include their original rows. If helpful, the budget page can also show the pre-reset historical total as audit context, but the launch guardrail uses only the active window.

Alternative considered: hide all pre-reset usage from the portal. Rejected because the reset is a budget-governance action, not an evidence-hiding action.

### Use deliberate wording and confirmation-level copy

Prefer labels like **Reset today's budget counter** or **Start new daily budget window**. Avoid **Reset token usage**, because it sounds like data deletion. The button copy must say ledger evidence, task actuals, and session reports are preserved.

Alternative considered: short destructive-looking wording with caveat text elsewhere. Rejected because this action changes guardrail behavior and needs literal-first operator trust.

## Risks / Trade-offs

- Reset waterline can make daily usage appear lower than full-day historical spend → mitigate by labeling it as current budget-window usage and preserving audit evidence elsewhere.
- Multiple reset timestamps in one day could be confusing → mitigate by using the latest reset as the active waterline and displaying it clearly.
- Consumers may drift if some still use midnight → mitigate with a shared helper and regression tests for dashboard, launch guardrail, and proxy/alarm paths.
- Reset at timezone boundaries can be subtle → mitigate by comparing reset timestamps against the existing local-day-start calculation in UTC ISO form.

## Migration Plan

- Existing installations have no reset timestamp, so behavior remains unchanged until the operator clicks reset.
- Saving budget caps must preserve any existing reset timestamp unless the reset action explicitly updates it.
- Rollback is safe: ignoring `daily_usage_reset_at` reverts to midnight-based daily usage without losing ledger evidence.

## Open Questions

None for the first slice. If operators later need history of every reset action, add an audit event/history table or setting log separately; the first slice only needs the latest active reset waterline.
