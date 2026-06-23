## Why

The OpenCode Worker Adapter records the configured Worker `workdir` as the subprocess cwd, but observed demo runs created files under the repository-level `incident-ledger/` directory instead of `.demo/opencode-comparison/harness-target`. OpenCode's `--dir` flag is the project-directory control used by the direct baseline runbook, so the harness must force that same project directory and detect mismatches after launch.

## What Changes

- Update OpenCode native launch command planning to include `--dir <adapter workdir>` whenever a workdir is configured, in addition to setting subprocess cwd.
- Preserve the selected Worker model, JSON event output, and scoped task prompt in the non-interactive `opencode run` command shape.
- Add post-run evidence that distinguishes the configured Worker workdir from any edited paths detected outside it.
- Mark a successful Worker process as a safety/launch evidence failure when the run produces no files or detected edits in the configured workdir but OpenCode evidence references edits elsewhere.
- Update tests to assert OpenCode launches are workdir-authoritative and that workdir mismatches are surfaced rather than treated as successful demo completion.
- Update the local OpenCode comparison runbook if needed so the portal and direct baseline describe the same `--dir` semantics.

## Capabilities

### New Capabilities

- `worker-workdir-enforcement`: Ensures Worker Adapter launches are bound to the configured project/workdir and records mismatch evidence when runtime edits occur elsewhere.

### Modified Capabilities

- `governed-worker-launch`: OpenCode launch command requirements change from merely setting process cwd to explicitly passing the configured workdir through OpenCode's project-directory argument.
- `worker-run-lifecycle`: Successful Worker process completion must preserve workdir/diff evidence and distinguish completed process evidence from completed work in the configured target.
- `long-opencode-comparison-demo`: The demo contract should require harness-created files to appear under `.demo/opencode-comparison/harness-target`, matching the configured adapter workdir.

## Impact

- Affected code: `src/agile_ai_htb/worker_adapters.py`, `src/agile_ai_htb/task_launch.py`, and related launch/evidence tests.
- Affected tests: `tests/test_worker_adapters.py`, launch lifecycle tests, and demo/runbook invariant tests as needed.
- Affected docs: OpenCode comparison runbook and any Worker Adapter setup text that implies cwd alone controls OpenCode's project root.
- No new external dependency is expected.
- Model-layer split remains unchanged: the control-plane/orchestrator model plans and routes; the OpenCode Worker Adapter launches native coding-worker models using OpenCode's own auth/config and selected Worker model.
