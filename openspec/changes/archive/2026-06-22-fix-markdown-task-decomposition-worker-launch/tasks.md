## 1. Reproduce and Lock Regression Tests

- [x] 1.1 Add a task API regression test where pasted markdown with three checklist items creates three persisted task cards, not one.
- [x] 1.2 Add a markdown upload regression test where uploaded `.md` content overrides pasted text and creates one task card per deterministic checklist item.
- [x] 1.3 Add assertions that each decomposed card description is scoped to the item and does not contain the full original markdown document.
- [x] 1.4 Add assertions that generated cards preserve source metadata: intake source, filename when present, decomposition index/count, and parent source identity.
- [x] 1.5 Add a Worker model constraint regression test showing a simple task does not select `opencode/big-pickle` just because it is first in discovered models.
- [x] 1.6 Add a Worker launch command regression test showing OpenCode command planning uses `opencode run --model <selected> --format json <prompt>` instead of bare `opencode`.

## 2. Markdown Decomposition Implementation

- [x] 2.1 Introduce a deterministic markdown task extraction helper for checklist/task bullets with conservative fallback when fewer than two items are found.
- [x] 2.2 Update `/tasks/estimate-form` to create and estimate multiple task rows when markdown extraction returns multiple items.
- [x] 2.3 Ensure each estimator call for a decomposed item uses scoped task text rather than the full original markdown body.
- [x] 2.4 Preserve markdown intake metadata on every generated card, including upload filename and decomposition ordering.
- [x] 2.5 Keep existing empty-input and unsupported-file validation behavior unchanged.

## 3. Worker Model Recommendation Fix

- [x] 3.1 Replace first-discovered-model fallback with a ranking function that considers estimate, complexity, and discovered model name signals.
- [x] 3.2 Prefer lightweight discovered models for simple/small tasks when available, including names containing `haiku`, `mini`, `nano`, or `flash`.
- [x] 3.3 Avoid heavyweight discovered models such as `big-pickle`, `opus`, `pro`, or `max` for simple/small tasks unless no lighter discovered model exists.
- [x] 3.4 Preserve constraint metadata with original estimator recommendation, available discovered models, selected model, and selection reason.

## 4. OpenCode Launch Command Fix

- [x] 4.1 Update the OpenCode Worker Adapter default launch command/preset to non-interactive `opencode run` with selected model, JSON output mode, and prompt.
- [x] 4.2 Ensure existing OpenCode adapter rows with bare `launch_template: ["opencode"]` are normalized at command-build time or blocked with a clear compatibility reason.
- [x] 4.3 Keep proxy-governed launch environment behavior unchanged: Harness Proxy URL and session API key are only applied for proxy-governed tracking.
- [x] 4.4 Keep native-usage launch evidence requirements unchanged: native mode is budget-authoritative only when trustworthy usage evidence is emitted.
- [x] 4.5 Ensure nonzero OpenCode exits preserve sanitized return code, stdout/stderr, selected adapter/model, and redacted command plan.

## 5. Verification

- [x] 5.1 Run targeted task API tests for markdown intake and model constraints.
- [x] 5.2 Run targeted Worker launch/budget tests for command planning and recoverable failure evidence.
- [x] 5.3 Run relevant estimator/decomposition eval tests.
- [x] 5.4 Run `uv run pytest` and verify the full suite passes.
- [x] 5.5 Manually run a local repro script or portal flow with a synthetic `.md` file to confirm multiple board cards are created and OpenCode launch command evidence is correct.
