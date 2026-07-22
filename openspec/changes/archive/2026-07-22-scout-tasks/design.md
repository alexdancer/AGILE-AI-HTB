## Context

ADR-0005 replaces the unimplemented hidden Spike concept with an ordinary `scout` Task kind. Current code already has most reusable seams: Tasks and breakdown candidates carry JSON metadata, estimation returns confidence, the completed two-surface change derives Needs You without new persistence, governed launches distinguish `read_only` from `write_capable`, Worker Runs land in Review, and Session Report exposes bounded evidence.

Two gaps matter. First, `task_breakdown_kind` is intake provenance rather than a canonical Task kind, and short intake cannot create investigation work. Second, current read-only behavior snapshots the repository before and after execution but does not prevent mutation; Codex native launch normalization explicitly converts a read-only sandbox to `workspace-write`. Scout launch therefore needs a distinct adapter capability, not merely a prompt or post-run diff.

This change depends on the completed `driver-based-token-estimation` and `two-surface-orchestration-board` changes being archived/synced before apply. The Estimator is a control-plane model; Scouts run through Worker/coding-harness adapters. Tracking mode remains a separate accounting/runtime-governance concern.

## Goals / Non-Goals

**Goals:**
- Make `scout` a canonical Task kind using the ordinary estimate → budget → Worker Run → Review lifecycle.
- Keep low-confidence recovery visible, advisory, operator-approved, and free of hidden Worker spend.
- Prevent Scout repository mutation before execution where the selected adapter supports a verified read-only profile, then retain unchanged-tree evidence.
- Reuse Task metadata, Needs You, Session Report, Worker accounting, and existing review disposition.
- Keep Scout evidence out of implementation coefficient fitting while allowing Scout-specific estimation context.

**Non-Goals:**
- No Spike endpoint, hidden subprocess, hidden orchestration usage, or automatic estimate rewrite.
- No Scout table, report table, generic workflow engine, or new lifecycle status.
- No adapter/provider unification and no change to tracking-mode authority.
- No write-capable fallback for an adapter without verified read-only enforcement.
- No recursive Scout creation, automatic repair Tasks, or automatic Scout disposition.

## Decisions

### Canonical Task kind lives in metadata

Use `metadata.task_kind` with exactly `implementation`, `scout`, or `acceptance_verification`. Direct short intake defaults to `implementation` and may explicitly select `scout`; Task Breakdown Review supports all three values. Accepted breakdown candidates copy `kind` to `task_kind` while retaining existing `task_breakdown_kind` as provenance during compatibility cleanup.

No DB column or migration is needed. The canonical reader prefers `task_kind`, then maps a valid legacy `task_breakdown_kind`, and only otherwise defaults to `implementation`. This preserves already-accepted legacy Acceptance Verification Tasks, preserves old rows, and avoids a second source of truth.

Alternative — infer Scout from title, prompt, or `read_only`: rejected because kind drives accounting, calibration, launch safety, and UI behavior.

### Scouts use ordinary estimation and Worker accounting

A Scout is estimated through the same control-plane Estimator and deterministic adapter-aware router as other Tasks. The Estimator receives task kind; Scout estimation constrains `files_to_modify` to zero and frames proof as bounded read-only investigation. Scout estimates remain nonzero because Worker execution consumes budget.

Worker usage is recorded as the Scout Task's `actual_tokens` under existing Worker accounting. It is never relabeled as orchestration spend. Calibration selection receives `task_kind`; implementation examples do not calibrate Scout estimates. Any coefficient-fitting input selector must require `task_kind == "implementation"`, so Scout actuals cannot fit implementation factors. Existing dashboard accuracy aggregates also remain implementation-only; Scout estimate/actual evidence stays visible on the Scout without silently changing implementation calibration indicators. This change does not add an automatic coefficient-fitting loop or a separate Scout accuracy dashboard.

Alternative — give Scouts a fixed or zero estimate: rejected because it hides real governed spend.

### Low confidence is a derived advisory decision

For non-Scout Tasks, automatic estimator confidence `< 0.60` creates a Needs You item without adding a lifecycle state or launch blocker. The operator may:

1. acknowledge and keep the estimate;
2. enter a manual estimate using existing task fields and manual-estimate provenance; or
3. create one linked Scout through the ordinary estimation path.

Minimal metadata on the implementation Task records the decision and linked Scout id; Scout metadata records `scout_for_task_id`. Needs You derives current action from that metadata plus both Tasks' authoritative lifecycle. A Scout does not offer creation of another Scout when its own estimate is low confidence; it offers acknowledgement or manual estimation only.

Create Scout uses a short `BEGIN IMMEDIATE` transaction as the ownership boundary: re-read the target and current `estimate_revision`; return the Scout already linked to that revision for an idempotent replay; otherwise create one visible Scout Task with `estimation_state: pending`, write both links plus the target revision, and commit before invoking the control-plane Estimator. Only the request that created that durable Scout invokes estimation. A concurrent request sees the existing revision-bound link and performs no second model call. Estimation success updates that Scout; failure preserves the same Scout with bounded failure/manual-recovery evidence, so retry cannot create a second Scout for that revision. A later low-confidence estimate revision may link a new Scout while old Scout Tasks retain their audit links. No external model call or Worker launch occurs while the database write transaction is open.

Creating a Scout does not change the target Task's estimate or lifecycle. While the Scout is Estimated or Running, the target decision is waiting. When the linked Scout has a completed Worker Run and is in Review or Done, Needs You offers review/re-estimation using its Session Report.

Alternative — persist a decision-queue table: rejected because the completed Needs You design is already a projection over existing records.

### Re-estimation is staged, bounded, and explicitly applied

The operator may request re-estimation only after a linked Scout has a completed Worker Run with a Session Report. The control-plane Estimator receives the original target Task context plus a sanitized, bounded Scout findings excerpt; raw command plans, arbitrary metadata, unbounded logs, local paths, and secrets are excluded.

The excerpt has one exact shape: `scout_task_id`, `session_id`, `worker_run_id`, `findings`, and `truncated`. IDs are strings capped at 200 characters. `findings` contains at most six chronological `detail.text` strings from `agent_message` events belonging to the linked Scout's latest completed Worker Run; non-dictionary details, non-string text, other event kinds/layers, stderr, tool calls, token events, command plans, and unknown fields are ignored. Canonical evidence redaction and project/home-path replacement run before each 2,000-character item bound and the 12,000-character aggregate bound. Malformed source collections produce no excerpt, and re-estimation remains unavailable rather than sending guessed or raw evidence.

Every canonical estimate/routing mutation increments `metadata.estimate_revision` (legacy default `0`). Re-estimation first atomically compare-and-sets `metadata.pending_reestimate` to `running` with an attempt id, source Worker Run id, and base estimate revision. A second request while that attempt is running or ready returns conflict before another control-plane call. Success compare-and-sets the same attempt to `ready` with source ids, computed estimate, drivers, confidence, routing evidence, rationale, and base revision; failure records bounded failure evidence on the same attempt. Process-crash recovery requires an explicit operator retry acknowledgement and preserves the abandoned attempt and possible duplicate control-plane spend rather than silently retrying.

The pending result does not alter `estimate_tokens` or `recommended_model`. A separate Apply transaction requires the same base `estimate_revision`, revalidates that the pending Worker model remains allowed for its selected/default adapter, copies the pending result into canonical estimate fields, increments the revision, and records explicit operator-application evidence. Stale revision or now-invalid routing returns conflict without partial changes. Dismiss records the decision and leaves the current estimate unchanged.

Alternative — apply the Estimator result immediately: rejected because it recreates Spike's silent rewrite. Alternative — manual-only re-estimation: rejected because the agreed flow permits an operator-requested Estimator rerun while preserving explicit application.

### Scout read-only safety is an adapter capability, not a tracking mode

Worker builders accept launch mode and expose whether an adapter has a verified adapter-enforced read-only profile. Scout launch requires all ordinary board launch checks plus this capability. `proxy_governed` and `native_usage` remain eligible only when their existing accounting evidence is authoritative; `observed_only` remains diagnostic-only.

For Codex, Scout command construction uses Codex's native `--sandbox read-only` mode and must not pass through the current workspace-write normalizer. Other adapters become Scout-launchable only after their own CLI permission/config profile is implemented and verified; prompt-only promises do not qualify. Unsupported adapters return a sanitized setup/compatibility reason before creating a Worker Run.

Before/after repository snapshots remain required as defense and audit evidence. A detected mutation remains a hard safety failure and enters the existing blocked-condition path, but detection is not used as the primary enforcement claim.

Alternative — reuse snapshot detection alone: rejected because it discovers mutation after user files may already have changed.

### Session Report is the Scout artifact

Scout prompts request a bounded report with findings, risks, and recommendation and prohibit writes, destructive commands, migrations, and commits. The existing Worker Run/Session Report is the authoritative artifact and audit surface. Cards and Needs You link to it; no second report format is introduced.

### Task Breakdown proposes Scouts sparingly

The Task Slicing Policy may return `scout` only when a bounded unanswered repository question materially prevents an honest implementation estimate or slice and the report has a concrete proof path. It must not emit generic research, speculative setup, or a Scout when ordinary implementation-time inspection is sufficient. Scout candidates preserve their question, inspection boundary, expected findings, proof, and target relationship when one exists.

## Risks / Trade-offs

- [Strict read-only support may initially enable only some adapters] → expose capability-specific launch reasons; never downgrade to prompt-only safety.
- [Metadata links can become stale after archive/dismiss actions] → derive state defensively, preserve ids as audit evidence, and show recovery instead of auto-creating replacements.
- [Scout output may contain secrets or excessive logs] → sanitize before truncation, use a bounded allowlisted findings excerpt for the Estimator, and keep full existing audit access in Session Report.
- [Concurrent estimate edits could apply stale Scout output] → bind `pending_reestimate` to the prior estimate and reject Apply on mismatch.
- [Low-confidence signals could flood Needs You] → threshold is fixed at `< 0.60`, acknowledgement is durable, and Scouts cannot recursively spawn Scouts.
- [Pending upstream changes are not yet canonical specs] → archive/sync `driver-based-token-estimation` and `two-surface-orchestration-board` before apply; revalidate this change after archive.

## Migration Plan

1. Archive/sync the two prerequisite completed changes; run strict spec validation.
2. Add read-compatible `task_kind` handling that preserves valid legacy `task_breakdown_kind` and otherwise defaults absent kind to `implementation`; no row rewrite required.
3. Add Scout intake/breakdown/estimation and low-confidence Needs You actions.
4. Add adapter read-only capability checks and verified launch-mode command construction before enabling Scout launch.
5. Add bounded Session Report re-estimation and explicit Apply behavior.
6. Update canonical terminology and focused tests, then run full backend/frontend/OpenSpec verification.

Rollback removes Scout creation/actions and capability checks. Existing Scout rows remain readable ordinary Tasks through metadata and existing lifecycle/report paths; no destructive data migration is required.

## Open Questions

None. Threshold, advisory behavior, explicit re-estimation application, strict read-only enforcement, creation surfaces, and report reuse were resolved during exploration.
