## 1. Prerequisites and Task-kind contract

- [x] 1.1 Verify `driver-based-token-estimation` and `two-surface-orchestration-board` are archived/synced; mechanically compare this change's already post-prerequisite Needs You and React MODIFIED blocks against the resulting canonical requirements, rebase only if archive output differs, and rerun strict OpenSpec validation before code edits.
- [x] 1.2 Add one canonical Task-kind validator/reader for `implementation`, `scout`, and `acceptance_verification`, preferring `metadata.task_kind`, preserving valid legacy `metadata.task_breakdown_kind`, and defaulting only otherwise-untyped legacy Tasks to `implementation`.
- [x] 1.3 Thread canonical Task kind through direct Task creation, Task Estimation input, bounded Task projections, history, and Worker Run metadata without adding a DB column or row migration.
- [x] 1.4 Add focused compatibility tests proving legacy Acceptance Verification kind is preserved, otherwise-untyped legacy Tasks read as implementation, and invalid kinds fail before Task creation or mutation.

## 2. Scout intake and Task Breakdown

- [x] 2.1 Extend Task Breakdown candidate schema, prompt, validation, manual recovery, and React kind selector to accept exactly `implementation`, `scout`, or `acceptance_verification`.
- [x] 2.2 Extend Task Slicing Policy and deterministic tests so Scouts are proposed only for bounded material uncertainty with a question, inspection boundary, expected findings, and proof—not generic research or implementation-time inspection.
- [x] 2.3 Copy accepted candidate kind into canonical `task_kind`, preserve existing breakdown provenance, and shape Scout estimation/Worker text from bounded investigation context.
- [x] 2.4 Add short project intake support for explicit Scout creation while preserving implementation as default and keeping Acceptance Verification in Task Breakdown Review.

## 3. Low-confidence Needs You workflow

- [x] 3.1 Add a shared `< 0.60` low-confidence predicate and derived Needs You item for automatic estimates without changing lifecycle state or launch eligibility.
- [x] 3.2 Add authenticated backend-authoritative actions to acknowledge the current estimate and enter a manual estimate, recording durable decision/provenance and returning negotiated JSON for React callers.
- [x] 3.3 Add Create Scout ownership transaction that atomically creates/links one visible pending-estimation Scout for the current estimate revision before the control-plane call, returns that Scout on replay/race, preserves prior-revision Scout audit links, records estimation failure on the same Task, leaves the target unchanged, and never starts a Worker automatically.
- [x] 3.4 Derive the exact bounded low-confidence Needs You item/action projection for decision-required, Scout pending/unavailable, findings-ready, re-estimation running/ready/failed, and recovery states; prevent Scout-from-Scout recursion and fail closed for malformed or cross-project links.
- [x] 3.5 Implement the exact project/task-scoped JSON mutation routes, request bodies, success envelope, revision/attempt-bound safe generated links, stale-binding rejection, and sanitized `404`/`409`/`422`/`503` outcomes specified by `needs-you-queue`.
- [x] 3.6 Add service/API concurrency tests proving threshold/advisory behavior, project isolation, one linked Scout and one initial Estimator invocation under a race, idempotent replay, same-Scout estimation failure recovery, exact projection bounds, and no partial writes on errors.

## 4. Scout estimation and explicit re-estimation

- [x] 4.1 Pass canonical Task kind into estimator and calibration selection; require Scout drivers to represent zero expected file modifications while preserving a nonzero computed estimate and ordinary adapter-aware routing.
- [x] 4.2 Build the exact Scout-findings extractor from at most six chronological `agent_message.detail.text` values on the linked Scout's latest completed Worker Run; apply canonical secret redaction and project/home-path replacement before 2,000-character item and 12,000-character aggregate bounds, and ignore every non-allowlisted field/type/layer.
- [x] 4.3 Add an estimate-revision mutation helper and operator-requested re-estimation compare-and-set: claim one `running` attempt before the control-plane call, reject concurrent/ready duplicates before spend, and persist ready or bounded failed evidence without changing canonical estimate fields.
- [x] 4.4 Add explicit acknowledged retry, Apply, and dismiss actions; preserve interrupted attempt evidence/duplicate-spend warning, reject stale revision or no-longer-allowed Worker routing, and atomically apply/increment revision with Scout provenance only after operator action.
- [x] 4.5 Ensure calibration selection, current implementation coefficient evidence selection, and existing dashboard estimation-accuracy aggregates accept only eligible `implementation` Tasks; do not add an unused fitting loop or separate Scout accuracy dashboard.
- [x] 4.6 Add adversarial tests for malformed events, oversized output, secrets, home/project paths, unknown keys, cross-run evidence, concurrent re-estimation, interrupted retry acknowledgement, no silent rewrite, stale/disallowed Apply, explicit dismiss, Worker-vs-orchestration accounting, and Scout exclusion from implementation calibration/accuracy.

## 5. Adapter-enforced read-only launch

- [x] 5.1 Extend adapter readiness/builders with a read-only launch capability separate from tracking mode; verified `proxy_governed`/`native_usage` accounting alone must not claim Scout compatibility.
- [x] 5.2 Add a verified Codex Scout command profile using `codex exec --json --sandbox read-only`, selected allowed model, and task-bound project root; bypass the current workspace-write normalizer only for forced read-only launch.
- [x] 5.3 Keep OpenCode, Claude Code, and custom adapters Scout-disabled unless their adapter-specific CLI permission profile is implemented and verified; return a sanitized compatibility reason instead of prompt-only fallback.
- [x] 5.4 Derive `launch_mode: read_only` server-side from `task_kind: scout`, reject incompatible client/metadata modes before Session or Worker Run creation, and never create a Task branch or commit path for Scouts.
- [x] 5.5 Preserve before/after repository snapshots and hard-safety Blocked Condition behavior as defense/evidence; record canonical Task kind and verified read-only profile on Session/Worker Run evidence.
- [x] 5.6 Shape Scout Worker prompts to request findings, risks, and recommendation while prohibiting writes, destructive commands, migrations, and commits; reuse canonical Session Report.
- [x] 5.7 Add command-construction, readiness, launch-guardrail, lifecycle, mutation-detection, and authoritative-usage tests, including a temporary-repo write-attempt denial for the verified Codex profile, Codex read-only never being rewritten to `workspace-write`, and observed-only remaining non-launchable.

## 6. React Pipeline, Floor, and review UX

- [x] 6.1 Add Implementation/Scout selection to short Pipeline intake and preserve existing negotiated intake outcomes and authoritative reload behavior.
- [x] 6.2 Add canonical `task_kind` to bounded Task/history projections and render a visible Scout label on Pipeline, Floor, history, Task Breakdown Review, Session Report linkage, and relevant Needs You items.
- [x] 6.3 Render only backend-projected low-confidence actions for every specified decision state, including missing-link and failed/interrupted recovery, with manual estimate input and sanitized backend errors but no local lifecycle/estimate authority.
- [x] 6.4 Add request/retry re-estimate, pending-result review, explicit Apply, and dismiss controls linked to canonical Scout Session Report evidence; map exact JSON outcomes and authoritatively reload after success/conflict.
- [x] 6.5 Add focused React tests for selector defaults, bounded kind/action rendering, safe links, three initial choices, linked Scout/re-estimation states, explicit duplicate-spend acknowledgement, separate Apply, and failure preservation.

## 7. End-to-end proof and documentation

- [x] 7.1 Add one deterministic synthetic Portal E2E scenario covering low-confidence Needs You → linked Scout creation → enforced read-only synthetic Worker completion → Session Report → pending re-estimate → explicit Apply, with no real provider, CLI, secrets, or repository mutation.
- [x] 7.2 Update `CONTEXT.md` and operator-facing copy to make Scout canonical and remove Spike from active terminology/orchestration-token classifications while retaining ADR history.
- [x] 7.3 Add a stale-reference/invariant check for active Spike terminology and Scout demo artifacts; keep synthetic evidence obviously labeled.

## 8. Verification

- [x] 8.1 Run focused backend tests for estimation, Task Breakdown, Needs You, launch guardrails, Worker lifecycle, accounting, and calibration.
- [x] 8.2 Run `npm run check` in `frontend/` and the focused synthetic Portal E2E Scout scenario.
- [x] 8.3 Run `uv run pytest`, `openspec validate scout-tasks --strict`, and `openspec validate --specs --strict --no-interactive`; resolve all new failures and actionable warnings.
