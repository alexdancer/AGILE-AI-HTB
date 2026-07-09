## Context

Today Task Estimation loads `guardrails.yaml` and passes `model_routing.task_complexity` into the estimator prompt. The estimator LLM returns both task sizing fields and `recommended_model`; code validates that model against guardrails, then `_constrained_recommended_model()` may replace it if the selected/default Worker Adapter does not allow it. Launch readiness validates allowed Worker models again.

That works mechanically, but the authority boundary is wrong: the stored recommendation can originate from a model the Worker Adapter cannot use, and the system corrects it after the fact. The operator-facing recommendation should already be compatible with the Worker Adapter selected for the task, or absent with explicit setup metadata when no approved Worker model is available.

## Goals / Non-Goals

**Goals:**
- Make stored task `recommended_model` adapter-aware and launch-compatible with the selected/default Worker Adapter's operator-approved allowed models.
- Keep the Control Plane estimator separate from Worker model selection: estimator returns sizing and complexity evidence; deterministic routing chooses the Worker model.
- Enforce guardrail model-routing policy and budget-aware clamp in code rather than relying only on estimator prompt obedience.
- Preserve provenance metadata for audit/debugging when routing selects, clamps, or cannot select a Worker model.
- Keep launch guardrails as a final pre-run safety check.

**Non-Goals:**
- No Worker Adapter discovery rewrite.
- No new model inventory table.
- No new provider abstraction or Worker credential handling.
- No schema migration unless implementation proves task metadata cannot carry routing provenance.
- No automatic expansion of allowed models from discovered or seeded inventory.
- No change to native/proxy/observed-only tracking authority semantics.

## Decisions

### 1. Estimator stops owning Worker model choice

`estimate_task()` should stop requiring the LLM to return `recommended_model`. It should return token estimate, complexity, confidence, rationale, assumptions, risk flags, budget note, and source. The prompt may still include complexity descriptions and budget context, but it should not ask the LLM to pick a Worker model.

Rationale: task sizing is an LLM-suitable judgment call; selecting a launchable Worker model is a policy/availability decision that the application can compute deterministically.

Alternative considered: keep `recommended_model` in estimator output and reject incompatible models earlier. That still makes the LLM the apparent source of a decision that depends on local adapter state it may not know.

### 2. Add a deterministic routing seam

Introduce a small routing function/module that takes:
- estimator complexity and token estimate,
- loaded guardrail model-routing policy,
- remaining/daily budget context,
- selected `adapter_id` or default adapter,
- `allowed_worker_model_ids(adapter)`.

It returns:
- `selected_model` or `None`,
- selected/default adapter id when known,
- guardrail policy candidate before adapter filtering,
- routing reason/state,
- budget clamp evidence,
- allowed-model inventory snapshot used for selection.

Rationale: this makes the recommendation reproducible, testable, and aligned with Worker Adapter constraints.

Alternative considered: keep `_constrained_recommended_model()` in `routes/tasks.py`. That preserves current behavior but keeps domain routing logic hidden inside an HTTP route.

### 3. Adapter allowed models are a hard recommendation source

When an adapter has operator-approved allowed models, `recommended_model` stored on the task must be one of them. If the guardrail policy candidate is not allowed, the router chooses an allowed substitute using the existing lightweight/heavyweight ranking pattern and complexity/token estimate.

Rationale: discovery proves availability, but operator-approved allowed models authorize governed recommendation and launch.

Alternative considered: recommend the guardrail model and show adapter substitute only at launch. That is the current confusing behavior the change removes.

### 4. Empty allowed models produce no static recommendation

If no selected/default adapter exists, or the adapter has no operator-approved allowed models, estimation may still create a task with token/complexity evidence, but it must not store a fake or assumed `recommended_model`. Metadata should explain `no_adapter` or `no_allowed_models` and the UI/launch guardrails should point the operator to Worker Setup.

Rationale: recommending an unusable static model is worse than showing setup-incomplete routing evidence.

Alternative considered: always fall back to the guardrail model. That violates the operator requirement because it can recommend a model the Worker Adapter cannot use.

### 5. Budget-aware clamp becomes deterministic

Use guardrails `budget_aware_clamp` after choosing the complexity policy candidate and before final adapter-compatible selection. If remaining daily budget is below the configured threshold, downgrade one complexity tier when possible and record clamp metadata. Final selection still must be from adapter allowed models.

Rationale: budget clamp is a policy rule, not merely a suggestion to the estimator.

Alternative considered: keep clamp in the prompt only. That leaves behavior nondeterministic and hard to test.

## Risks / Trade-offs

- [Risk] Existing tests and clients expect estimator JSON to include `recommended_model`. → Update the estimator contract tests, API route tests, fake LLMs, and any documentation/spec references together.
- [Risk] Tasks with estimates but no recommended model may not fit current board assumptions. → Preserve clear metadata and tests for no-adapter/no-allowed-model behavior; keep launch guardrails blocking before process start.
- [Risk] Guardrails routing models may not literally match every adapter's model IDs. → Treat guardrails as tier policy candidates and adapter allowed models as final candidates; use deterministic ranking to map tier intent onto allowed model IDs.
- [Risk] Ranking by model name is imperfect. → Keep simple, explicit heuristics for the first slice and preserve routing metadata so operators can override before launch.
- [Risk] Updating calibration examples could conflate historical evidence with current available models. → Keep calibration model fields as examples/provenance, but do not let them override deterministic adapter-aware routing.

## Migration Plan

1. Add routing tests around direct guardrail match, adapter substitution, no adapter, no allowed models, simple-task lightweight preference, large-task heavyweight preference, and budget clamp.
2. Update estimator schema/prompt/parser to remove LLM-owned `recommended_model`.
3. Move route-level model constraint logic into the deterministic routing seam.
4. Update `/estimate` and Markdown intake accepted-candidate estimation to call routing before task creation.
5. Update board/API assertions and fake estimator fixtures.
6. Run targeted estimator, task-estimation, board launch selection, Worker adapter allow-list, and launch guardrail tests, then full `uv run pytest`.

Rollback is straightforward: revert the routing module and estimator contract changes; no persisted schema migration is expected for this first slice.
