## 1. Shared Portal primitives

- [x] 1.1 Consolidate repeated inline page/card/action/alert/empty-state styles into shared classes in `base.html` without adding a frontend build step.
- [x] 1.2 Update dashboard, project, board, setup, workers, sessions, alarms, and report templates touched by this change to use the shared classes for common patterns.
- [x] 1.3 Add or adjust rendered-page tests proving common action cards, alerts, empty states, and responsive/wide-content wrappers still render.

## 2. Project workspace overview

- [x] 2.1 Derive selected-project task counts, running/review counts, readiness, and relevant action targets from existing database helpers in the project workspace route.
- [x] 2.2 Render a compact project action/readiness summary before repo profile details on `/projects/{project_id}`.
- [x] 2.3 Add tests for project overview next actions, preserved repo profile details, and links to existing board/setup/session workflows.

## 3. Project board readability

- [x] 3.1 Add a compact board operating-status toolbar for project identity, column counts, Worker readiness, and active run/automation status using existing route data.
- [x] 3.2 Add lifecycle-specific empty states for board columns without changing board statuses or launch/review forms.
- [x] 3.3 Distinguish launch failure, launch guardrail block, human Blocked disposition, and manual-estimate copy on task cards.
- [x] 3.4 Preserve Worker Adapter/model/tracking clarity in launch controls, including actual run model before estimator recommendation when different.
- [x] 3.5 Add board template tests for toolbar counts, empty states, error/block copy, and model-layer labels.

## 4. Setup and readiness guidance

- [x] 4.1 Add a next-missing-action summary to setup/Worker Adapter pages using existing adapter/project/model/tracking readiness data.
- [x] 4.2 Move verbose adapter diagnostics, verification evidence, and tracking details behind native details sections while preserving access.
- [x] 4.3 Add setup/worker portal tests for setup-needed, launch-ready, no allowed models, and diagnostic disclosure states.

## 5. Evidence readability

- [x] 5.1 Add a concise evidence summary to session/report surfaces for launch target, Worker Adapter, Worker model, tracking mode, status/result, token usage, alarms, and review state when available.
- [x] 5.2 Keep raw stdout/stderr, command evidence, timeline events, and Agent Review findings behind secondary details unless they are the primary failure message.
- [x] 5.3 Add rendered-page tests for summary-first evidence, missing-evidence labels, and raw evidence disclosure.

## 6. Verification and docs

- [x] 6.1 Run targeted portal tests covering projects, board, dashboard, workers/setup, sessions/reports, and alarms.
- [x] 6.2 Run `openspec validate improve-portal-quality --strict` or the repo's equivalent OpenSpec validation command.
- [x] 6.3 Run full `uv run pytest` after targeted tests pass.
- [x] 6.4 Update `CONTEXT.md` only if implementation introduces new product terminology; otherwise leave domain docs unchanged.
