## 1. Launch lifecycle and recoverable failure semantics

- [x] 1.1 Add tests proving an Estimated task whose Worker command times out or exits nonzero returns to its exact pre-launch status, records failed session evidence, stores sanitized `launch_error`/`last_launch_failure` metadata, and remains eligible for relaunch.
- [x] 1.2 Add tests proving missing proxy-governed or native-usage evidence after a launch attempt is treated as a recoverable launch failure for launchable tasks while still failing the Worker session and preserving strong guardrail copy.
- [x] 1.3 Update `src/agile_ai_htb/task_launch.py` to preserve/restore the pre-launch task status for recoverable Worker runtime failures instead of moving launchable tasks to `Blocked`.
- [x] 1.4 Keep hard safety and lifecycle failures blocking: non-launchable preconditions, manual-estimate requirements, unverified/unavailable adapters, incompatible Worker models, read-only project mutation, and write-capable verification failure.
- [x] 1.5 Clear or supersede stale recoverable launch-error metadata on a successful retry while preserving normal successful launch/session evidence.

## 2. Board launch error display

- [x] 2.1 Add board/route tests proving recoverable launch failures render inline on the affected task card and the launch form remains visible.
- [x] 2.2 Update `src/agile_ai_htb/templates/board.html` to render recoverable `launch_error`/`last_launch_failure` sanitized evidence separately from workflow `blocked_reason` and `launch_blocked_reason`.
- [x] 2.3 Update launch redirect/error handling in `src/agile_ai_htb/routes/tasks.py` as needed so board-level setup/guardrail errors still use the dismissible banner while task-specific recoverable runtime errors appear on the card.
- [x] 2.4 Add/adjust tests proving the Blocked column is reserved for dependency/workflow/safety blockers and not normal Worker timeout retry states.

## 3. Configurable local/demo Worker timeout

- [x] 3.1 Add tests for `subprocess_runner()` showing adapter/command-plan timeout metadata overrides the default timeout without real sleeps.
- [x] 3.2 Extend the Worker command plan or adapter config path to carry `timeout_seconds` into `src/agile_ai_htb/worker_adapters.py`.
- [x] 3.3 Configure the `demo_worker` launch path to use an extended timeout suitable for multiple real proxy model calls while leaving generic Worker adapters on the safe default.
- [x] 3.4 Ensure timeout error output continues to be sanitized and records the actual timeout value used.

## 4. Markdown task intake

- [x] 4.1 Add board/API tests for pasted multi-line markdown task descriptions submitted through `/tasks/estimate-form`.
- [x] 4.2 Add board/API tests for uploaded `.md` files submitted through `/tasks/estimate-form`, including redirect back to `/board` and persisted markdown source metadata.
- [x] 4.3 Add tests proving uploaded `.md` content wins over pasted textarea content when both are submitted.
- [x] 4.4 Add tests proving empty markdown and unsupported uploaded file types show validation errors and do not create tasks.
- [x] 4.5 Update `src/agile_ai_htb/templates/board.html` to replace the one-line estimator input with a markdown textarea plus optional `.md` upload control using multipart form encoding.
- [x] 4.6 Update `src/agile_ai_htb/routes/tasks.py` to normalize pasted/uploaded markdown into the existing estimator request path and record deterministic intake source metadata.

## 5. Estimator decomposition behavior evals

- [x] 5.1 Add synthetic markdown fixtures using obvious DEMO identifiers and 2099 dates for repo-aware, long-form, and bullet-point task inputs.
- [x] 5.2 Add eval/test coverage proving repo-aware markdown input produces estimated work with token estimates, recommended Worker-compatible models when applicable, and markdown intake metadata.
- [x] 5.3 Add eval/test coverage proving bullet-point or phased markdown tasks become multiple estimated tasks or explicit structured breakdown metadata.
- [x] 5.4 Add eval/test coverage proving complex markdown that cannot be safely estimated produces a specific manual-estimate or rejection reason, not vague null/uncertain output.
- [x] 5.5 Add or update fake-data invariant checks so estimator demo fixtures cannot contain real-looking accounts, addresses, dates, credentials, or non-DEMO values.

## 6. Budget alarm behavior evals

- [x] 6.1 Add behavior-level alarm tests for yellow/red budget zone transitions using synthetic Worker execution usage.
- [x] 6.2 Add behavior-level alarm tests for daily cap and session cap boundary crossings.
- [x] 6.3 Add tests proving repeated alarm detection over the same evidence does not create duplicate visible alarms.
- [x] 6.4 Add dashboard and session-report tests proving generated budget alarms are visible in both operator surfaces.
- [x] 6.5 Add tests proving control-plane/task-breakdown/adapter-verification/reporting spend does not reduce Worker execution launch budget or trigger Worker execution alarms.

## 7. Verification and OpenSpec bookkeeping

- [x] 7.1 Run targeted tests for launch lifecycle, board rendering, markdown intake, timeout handling, estimator evals, and alarm behavior.
- [x] 7.2 Run full `pytest` and fix regressions caused by the lifecycle semantics change.
- [x] 7.3 Run OpenSpec validation/status commands for `fix-local-demo-launch-and-task-intake-evals` and resolve artifact/spec formatting issues.
- [x] 7.4 Mark completed tasks in this file only after the corresponding implementation and verification pass.
