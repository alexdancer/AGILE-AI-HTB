## Why

Low-confidence estimation currently has no governed investigation path: operators either accept a weak estimate or replace it manually. ADR-0005 chooses visible Scout Tasks over hidden Spike orchestration so investigation uses the normal Worker pipeline, records real Worker spend, and never silently rewrites an estimate the operator has already seen.

## What Changes

- Add `scout` as a first-class Task and Task Breakdown candidate kind alongside `implementation` and `acceptance_verification`.
- Let operators create Scouts from short project intake or Task Breakdown Review; let the Task Breakdown Agent propose them when bounded investigation is the smallest useful slice.
- Treat estimator confidence below `0.60` as advisory Needs You work with explicit actions to accept the estimate, enter a manual estimate, or create a linked Scout. Low confidence does not block launch by itself.
- Run Scouts as ordinary estimated, budgeted Worker Tasks that force read-only launch, produce the existing Session Report as their findings artifact, and land in Review.
- Require adapter-enforced read-only execution for Scout launch, retaining before/after repository checks as defense and evidence; adapters without a verified read-only profile cannot launch Scouts.
- Allow a completed linked Scout report to be supplied as bounded context for an operator-requested re-estimate. The operator must explicitly apply the result; the Harness never rewrites a seen estimate automatically.
- Record Scout usage as Worker actuals on the Scout Task and exclude Scout actuals from implementation accuracy aggregates and coefficient fitting.
- Remove remaining Spike terminology from canonical product documentation and orchestration-token classifications.

## Capabilities

### New Capabilities
- `scout-tasks`: first-class Scout creation, linkage, low-confidence decision flow, visible Worker accounting, bounded findings, explicit re-estimation, and calibration isolation.

### Modified Capabilities
- `task-breakdown-review`: candidate kind expands to `implementation`, `scout`, or `acceptance_verification`, with Scout-specific prompt and context preservation.
- `governed-worker-launch`: read-only Scout launch requires an adapter-enforced read-only profile and preserves unchanged-repository evidence while using the normal governed Worker lifecycle.
- `react-board-workflow`: bounded Pipeline/Floor task projections and short intake expose canonical Task kind so Scouts are explicit without leaking raw metadata.
- `needs-you-queue`: low-confidence estimate decisions join Needs You as advisory work without becoming a lifecycle status or a launch blocker.
- `estimation-accuracy-tracking`: existing dashboard accuracy aggregates remain implementation-only while Scout estimate/actual evidence stays visible on the Scout Task.
- `project-task-history`: bounded history task entries expose canonical Task kind so archived Scouts remain distinguishable without exposing raw metadata.

## Impact

- Backend: task intake/estimation routes, Task Breakdown schema and acceptance, Needs You projection/actions, Worker launch capability checks and adapter command construction, bounded re-estimation context, task metadata, and coefficient fitting selection.
- Frontend: Pipeline short intake, Needs You actions, Task Breakdown Review kind selector, Scout badges/linkage, Session Report/re-estimation actions, and sanitized bounded projections.
- Worker Adapters: read-only capability verification and Scout command profiles remain separate from tracking mode (`proxy_governed`, `native_usage`, or `observed_only`); `observed_only` remains non-launchable.
- Dependencies: apply after the completed `driver-based-token-estimation` and `two-surface-orchestration-board` changes are archived/synced, because this change extends their confidence, coefficient, Pipeline, and Needs You contracts.
- Non-goals: no Spike dispatch path, no hidden orchestration spend, no automatic estimate rewrite, no Scout-specific table, no new report format, no Worker model/provider unification, no write-capable Scout fallback, and no automatic repair-task creation.
