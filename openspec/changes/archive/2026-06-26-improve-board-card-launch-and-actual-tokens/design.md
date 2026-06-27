## Context

The board already has compact cards with expandable details, and session reports already calculate token totals from `token_turns`. The missing link is task-level persistence: successful Worker Run completion records session/token evidence but does not fill `tasks.actual_tokens`, so completed/reviewed cards can show no actual token total. The board also treats `launch_stdout` as evidence that the `Launch` section exists, but the section only renders error/blocked/failure fields, so successful runs can expose a blank `Launch` disclosure.

## Goals / Non-Goals

**Goals:**

- Persist task `actual_tokens` from authoritative Worker execution usage when a successful Worker Run reaches Review.
- Keep Done disposition evidence-preserving: Mark Done must not erase or recompute the recorded actual token total.
- Make board cards show actual token totals for Review/Done tasks when available.
- Make `Launch` details non-empty when rendered, using existing Worker Run/task metadata.

**Non-Goals:**

- No board redesign, SPA, websocket stream, or new details component.
- No schema migration; reuse `tasks.actual_tokens`, `token_turns`, `worker_runs`, and existing metadata.
- No new token accounting category.
- No change to Worker Adapter auth/model selection.

## Decisions

### Use Worker execution token totals for `tasks.actual_tokens`

`tasks.actual_tokens` will mean actual Worker execution tokens for the task, not all control-plane tokens attached to the session. Implementation should derive it from `db.session_token_breakdown(...)["by_category"]["worker_execution"]` when completion evidence is accepted.

Alternatives considered:

- Total session tokens: easier, but mixes estimation/reporting/review tokens into task execution cost.
- Compute only in the template: avoids persistence, but leaves estimation accuracy and API/task consumers without the completed actual value.

### Set actual tokens at Worker Run success, not at Mark Done

The Worker Run completion path is where the authoritative evidence is checked and the task enters Review. Mark Done should preserve the value, not become the first place that calculates it.

Alternatives considered:

- Set during Mark Done: misses Review cards and makes token recording dependent on human disposition.
- Background reconciliation: more moving parts for a value already available in the completion path.

### Keep `Launch` but make it evidence-backed

`Launch` should mean Worker launch/run evidence: selected adapter/model/tracking mode, command plan/cwd/workdir evidence, return code, and any failure/blocked details. If none of that is available, the section should not render blank; use an explicit unavailable message only when the section is important enough to render.

Alternatives considered:

- Rename to `Worker Run`: clearer, but larger copy churn. Keep `Launch` for now and populate it.
- Hide all launch details on success: shorter, but loses the audit trail operators expect.

## Risks / Trade-offs

- **Risk:** Native/proxy accounting can record zero Worker execution tokens for malformed evidence. → **Mitigation:** preserve `0` as a real value and distinguish it from unavailable/null in the UI.
- **Risk:** Launch command plans may include sensitive values. → **Mitigation:** render only already-sanitized/redacted persisted evidence and bounded raw blocks.
- **Risk:** Multiple Worker Runs for one task can exist after retry. → **Mitigation:** use the accepted session linked to the successful run/task for actual token persistence, and display latest/active Worker Run evidence consistently with existing board behavior.
