## Why

Markdown task intake currently accepts multi-task `.md` input but persists it as one oversized card, causing inflated estimates and poor Worker model recommendations. OpenCode launch also uses the bare `opencode` command, which can fail with return code 1 because the harness is not invoking the non-interactive `opencode run` command with the selected model and prompt.

## What Changes

- Decompose markdown intake into separate task cards when the uploaded or pasted markdown contains explicit task/checklist/phase items.
- Estimate each decomposed card from only its scoped task text while preserving source metadata that ties the cards back to the original markdown input.
- Keep single-card behavior for markdown that has no deterministic task items.
- Improve Worker model recommendation constraints so discovered model ordering does not cause simple tasks to choose heavyweight defaults such as `opencode/big-pickle`.
- Fix the OpenCode Worker Adapter launch template so governed Worker runs use non-interactive `opencode run --model {model} --format json {prompt}` style invocation instead of the bare CLI command.
- Preserve the existing Worker Adapter/tracking-mode split: OpenCode remains the local Worker Adapter; `proxy_governed`, `native_usage`, and `observed_only` remain separate usage-authority paths.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `markdown-task-intake`: Markdown task intake must create multiple task cards for deterministic task lists instead of only recording breakdown metadata on one card.
- `estimator-task-decomposition-evals`: Evals must assert separated cards and scoped per-card estimates for markdown task lists.
- `native-worker-model-discovery`: Worker model recommendation constraints must select an appropriate discovered model by task size/intent rather than blindly choosing the first discovered model.
- `governed-worker-launch`: OpenCode launch command planning must invoke the selected Worker model through non-interactive `opencode run` and preserve sanitized failure evidence when launch fails.

## Impact

- Affected code: `src/agile_ai_htb/routes/tasks.py`, `src/agile_ai_htb/estimation.py`, `src/agile_ai_htb/db.py`, `src/agile_ai_htb/worker_adapters.py`, `src/agile_ai_htb/task_launch.py` as needed.
- Affected tests: task API markdown intake tests, estimator/decomposition eval tests, model recommendation constraint tests, Worker launch command planning tests.
- Affected UI behavior: Board markdown upload/paste can create several Estimated cards from one input file, each with source/decomposition metadata.
- No new external dependencies are expected.
