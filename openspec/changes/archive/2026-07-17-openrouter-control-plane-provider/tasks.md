## 1. Transport — `src/foreman_ai_hq/llm.py`

- [x] 1.1 Add `openrouter` to the OpenAI-compatible provider set in `acompletion` so it routes through `_openai_compatible_completion`.
- [x] 1.2 Add `DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"` and return it from `_provider_base_url` for provider `openrouter` when no base URL is configured.

## 2. Cost capture — `src/foreman_ai_hq/llm.py`

- [x] 2.1 Add `extract_cost(response) -> float | None` that reads `usage.cost` (tolerating missing/None/non-numeric), keeping `cost_details.upstream_inference_cost` available as evidence only.
- [x] 2.2 Add `resolve_cost(model, response) -> float | None` that returns `extract_cost(response)` when not None, else `_calculate_known_cost(model, prompt_tokens, completion_tokens)` derived from `extract_usage(response)`. Leave `extract_usage` (tokens only) and `_calculate_known_cost` unchanged.
- [x] 2.3 Update the three Control Plane orchestration call sites (`routes/tasks.py:339`, `routes/tasks.py:909`, `routes/tasks.py:1521`) and the proxy-governed Worker accounting seam (`routes/proxy.py:97`) to pass the response through `resolve_cost`. Confirm each already has the full response object in scope.
- [x] 2.4 In the control-plane connection-test handler (`routes/portal.py:1326`), record the resolved cost (`resolve_cost(model, response)`) in the test evidence alongside `extract_usage`, keeping key redaction unchanged.

## 3. Settings / validation plumbing

- [x] 3.1 Widen the provider regex in `routes/portal.py:213` to `^(openai|anthropic|openai-compatible|openrouter)$`.
- [x] 3.2 Add an OpenRouter "recommended for orchestration" shortlist to `CURATED_CONTROL_PLANE_MODELS` (`routes/portal.py:256`) — a few strong tool-use IDs (e.g. `anthropic/claude-sonnet-*`, `openai/gpt-*`, `google/gemini-*`); verify current IDs against OpenRouter before hard-coding.
- [x] 3.3 In `operator_config.py` / `settings.py`, accept provider `openrouter`, default `api_key_env=OPENROUTER_API_KEY`, and auto-fill the base URL. Reuse `write_control_plane_secret` / `load_operator_secrets_env`; do not fan the key out into unrelated provider env vars.

## 4. Frontend — `frontend/src/views/ControlPlaneSettings.jsx`

- [x] 4.1 Add `openrouter` to `PROVIDERS` (`:11`), labeled to read as recommended.
- [x] 4.2 Confirm the existing curated `<select>` + custom-model fallback renders the OpenRouter shortlist and accepts a custom OpenRouter model ID; no picker rewrite.
- [x] 4.3 In the connection-test panel (`~:364`), render a Cost line beside "Total tokens" from the resolved cost; when cost is unavailable, show an explicit "unavailable" label rather than `$0.00`.

## 5. Verification

- [x] 5.1 Unit: `_provider_config` resolves the OpenRouter base URL; provider regex accepts `openrouter`; `resolve_cost` returns reported `usage.cost` when present and `None`-falls-back to `_calculate_known_cost` when absent (OpenAI path unchanged).
- [x] 5.2 Unit: an OpenRouter-shaped fake response with `usage.cost` records the reported cost at a Control Plane call site; a response without cost records the computed-or-null value.
- [x] 5.3 Unit/behavioral: the connection-test evidence includes the resolved cost; the settings view renders a dollar Cost line when cost is present and an "unavailable" label (not `$0.00`) when it is not.
- [x] 5.4 Manual e2e (real OpenRouter key): `foremanctl serve` → `/settings/control-plane` → select OpenRouter → paste key → pick a model → connection test passes and shows a dollar Cost line → an estimator/breakdown run records spend as Orchestration Tokens with a non-null dollar cost.
- [x] 5.5 Regression: point Advanced `openai-compatible` at local Ollama (`http://localhost:11434/v1`, dummy key) and confirm transport, token accounting, and known-model pricing behavior are unchanged; unresolved cost follows the shared nullable-ledger contract.
- [x] 5.6 Gates: `uv run pytest -q`, `npm --prefix frontend run check`, `openspec validate openrouter-control-plane-provider --strict`.

## 6. Verification remediation

- [x] 6.1 Make `token_turns.cost` nullable through an idempotent migration, preserve existing numeric values, and pass `resolve_cost(...)` results through without `None` → `0.0` coercion at every scoped call site.
- [x] 6.2 Add persistence coverage proving reported cost remains numeric while unresolved cost remains database `null`.
- [x] 6.3 Isolate Control Plane route tests from repo-local `.foreman` config/secrets and add an explicit uncurated OpenRouter custom-model render/save regression.
- [x] 6.4 Re-run targeted tests, frontend check/build, default full pytest, strict whole-repo OpenSpec validation, and independent review.
