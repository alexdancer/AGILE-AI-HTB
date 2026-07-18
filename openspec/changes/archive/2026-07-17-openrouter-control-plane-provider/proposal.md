## Why

Configuring the Control Plane model today means picking `openai` / `anthropic` /
`openai-compatible` and pasting a raw per-provider API key, which the operator dislikes and
which reaches only one provider per key. OpenRouter is an OpenAI-compatible aggregator that
gives many models behind a single key and — uniquely — returns the real dollar `cost` on
every response. This slice adds OpenRouter as a first-class Control Plane provider and, riding
that, captures truthful per-call cost instead of the current hard-coded 3-model estimate.

This is **Slice 1** of `docs/OPENROUTER_CONTROL_PLANE_PLAN.md`. It deliberately excludes the
OAuth "Connect" button (Slice 2) and the searchable live catalog picker (Slice 3); an operator
uses OpenRouter here by pasting one OpenRouter key.

## What Changes

- Route provider `openrouter` through the existing OpenAI-compatible transport, defaulting the
  base URL to `https://openrouter.ai/api/v1` when none is set.
- Accept `openrouter` in the Control Plane provider validation and settings/config plumbing,
  defaulting its key env name to `OPENROUTER_API_KEY` and auto-filling the base URL.
- Add an OpenRouter "recommended for orchestration" shortlist to the single authoritative
  curated model list; the frontend gains `openrouter` as a provider reusing the existing model
  select + custom-id fallback.
- **Capture real cost:** prefer the response's `usage.cost` for Control Plane usage accounting,
  falling back to the existing computed price when a provider reports no cost. This mirrors the
  Worker-side precedent already in `native_usage.py`. Token accounting is unchanged (OpenRouter
  returns OpenAI-shaped `usage`, so counts flow through the existing path for free).
- Preserve unresolved cost as database `null` rather than coercing it to `$0.00`, so an unpriced
  call remains distinguishable from a genuinely free call throughout persisted evidence.
- **Show the cost:** surface the resolved dollar cost in the Control Plane settings UI where it
  already shows token usage — the connection-test panel gains a Cost line (test handler resolves
  cost; `$0.00` is never shown for an unavailable cost). Today every cost display in the UI is
  Worker-side; this is the first control-plane cost surface, so the slice's value is visible.
- Existing `openai` / `anthropic` / `openai-compatible` token accounting and known-model computed
  prices remain unchanged. Newly unresolved costs intentionally persist as `null` instead of the
  legacy call-site coercion to `0.0`, including proxy-governed Worker turns in the shared ledger.

Non-goals (later slices): OAuth PKCE Connect button; searchable live `/models` catalog picker;
per-provider OAuth for direct OpenAI/Anthropic (does not exist); any Worker Adapter change.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `control-plane-model-connection`: add OpenRouter as an accepted Control Plane provider
  (transport routing, default base URL, curated shortlist, single-key usage); add
  provider-reported cost accounting so Control Plane usage prefers the response's `usage.cost`
  over the computed estimate; and add a requirement that the resolved cost is shown in the
  settings UI where token usage is already shown. Provider transport and preset behavior remain
  unchanged; unresolved-cost persistence becomes nullable across the scoped shared-ledger callers.

## Impact

- Code:
  - `src/foreman_ai_hq/llm.py` — `acompletion` provider set, `_provider_base_url` default,
    new `extract_cost` + `resolve_cost(model, response)`.
  - `src/foreman_ai_hq/routes/portal.py` — provider regex (`:213`) and
    `CURATED_CONTROL_PLANE_MODELS` (`:256`) gain `openrouter`.
  - `src/foreman_ai_hq/routes/tasks.py` (`:339`, `:909`, `:1521`) and
    `src/foreman_ai_hq/routes/proxy.py` (`:97`) — call sites switch to `resolve_cost`.
  - `src/foreman_ai_hq/operator_config.py` / `settings.py` — accept provider `openrouter`.
  - `frontend/src/views/ControlPlaneSettings.jsx` — `PROVIDERS` gains `openrouter`; the
    connection-test panel gains a Cost line.
  - `src/foreman_ai_hq/routes/portal.py` (`:1326`) — the control-plane test handler records the
    resolved cost alongside usage.
- APIs/config: new accepted provider value `openrouter`; default key env `OPENROUTER_API_KEY`.
- Dependencies: none (reuses existing OpenAI-compatible client and secret storage).
- Database: migrate `token_turns.cost` from required to nullable so unresolved provider cost can
  remain `null`; existing numeric values are preserved. This also affects proxy-governed Worker
  turns using the shared ledger, without changing Worker Adapters.
