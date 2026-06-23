## 1. Command Planning

- [x] 1.1 Update `WorkerAdapterBuilder` so OpenCode native launch plans include `--dir <configured workdir>` when a workdir is configured, while preserving subprocess cwd.
- [x] 1.2 Update OpenCode native verification command planning to include the same `--dir <configured workdir>` behavior.
- [x] 1.3 Add normalization logic so existing/custom OpenCode templates do not launch as bare `opencode` and do not duplicate `--dir` when already present.

## 2. Workdir Evidence and Mismatch Handling

- [x] 2.1 Add helpers to collect configured-workdir evidence for Worker Runs, including whether the workdir exists, top-level files, and git/filesystem change evidence when available.
- [x] 2.2 Parse or scan sanitized OpenCode stdout/stderr/native event evidence for absolute paths outside the configured workdir that indicate read/write activity.
- [x] 2.3 Mark successful Worker process exits as retryable workdir mismatch failures when configured-target evidence is empty and outside-path evidence is present.
- [x] 2.4 Preserve configured workdir, command cwd, selected adapter/model, redacted command plan, and suspicious outside paths in Worker Run/task metadata.

## 3. Tests

- [x] 3.1 Update `tests/test_worker_adapters.py` to assert default OpenCode native launch and verification commands include `--dir` with the configured workdir.
- [x] 3.2 Add tests covering custom OpenCode templates that already include `--dir` and templates that omit it.
- [x] 3.3 Add Worker Run lifecycle tests for the observed failure mode: return code 0, native usage evidence present, outside-path evidence points to repo-level `incident-ledger`, and configured `harness-target` has no files.
- [x] 3.4 Add a positive Worker Run lifecycle test where configured-workdir evidence exists and the run proceeds to Review normally.

## 4. Demo Documentation and Verification

- [x] 4.1 Update the OpenCode comparison runbook to state that harness launches must pass OpenCode `--dir` and that harness output must appear in `.demo/opencode-comparison/harness-target`.
- [x] 4.2 Add or update demo invariant tests so misplaced harness output is not counted as successful harness evidence.
- [x] 4.3 Run targeted tests for worker adapter command planning, Worker Run lifecycle, and demo invariants.
- [x] 4.4 Run the broader `pytest` suite or document any blocker with the exact failing command/output.
