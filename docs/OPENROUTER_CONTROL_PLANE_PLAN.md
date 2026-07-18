# Control Plane: OpenRouter + OAuth as the low-friction model front door

**Status:** Planned (not started)
**Scope:** Control Plane orchestration model connection only. **Not** ACP / Worker Adapters.

## Context

The operator dislikes the current Control Plane model setup, which requires picking a
provider (`openai` / `anthropic` / `openai-compatible`) and **pasting a raw API key**
into `/settings/control-plane`. The request originally came in framed as "replace the
Control Plane with ACP," but that rests on a scope error that must not survive into
implementation:

- **ACP (Agent Client Protocol)** is a JSON-RPC-over-stdio standard for launching and
  observing a *coding-agent Worker* (Claude Code, Gemini). Per `docs/TODO.md` and
  `CONTEXT.md` it is a **Worker Adapter transport**, is *control/observe only* (no token
  accounting), and must sit on top of an existing Tracking Mode. It does **not** touch the
  Control Plane orchestration model and cannot remove the key-pasting pain. **ACP is
  explicitly out of scope here** and stays a separate future Worker item in TODO.md.
- The real goal is a **low-friction, multi-provider Control Plane model connection**:
  sign in instead of pasting keys, and reach many models. Per-provider OAuth for API
  billing largely does not exist (OpenAI/Anthropic API access = API key). The one path that
  delivers OAuth **and** many-providers **and** open access together is **OpenRouter**,
  an OpenAI-compatible aggregator with a real OAuth PKCE flow.

**Outcome:** Add OpenRouter as the recommended default Control Plane provider with an
OAuth "Connect" button and a searchable model catalog, riding the existing
OpenAI-compatible transport. Direct `openai`/`anthropic`/`openai-compatible` stay as
Advanced options (existing code + tests untouched). Control Plane calls keep returning
OpenAI-shaped `usage`, so Orchestration-Token accounting stays truthful.

## Locked decisions

1. Solve the Control Plane key friction, **not** ACP (ACP deferred, stays a Worker item).
2. Front door = **OpenRouter + OAuth PKCE** (only path giving OAuth + many models + open access).
3. OpenRouter is the **recommended default**; `openai`/`anthropic`/`openai-compatible`
   demoted to an **Advanced** group, kept working.
4. Model picker = **recommended shortlist + custom-id fallback**; the searchable live
   catalog is optional UX polish (Slice 3), no longer needed for pricing.
5. **Cost comes from the response, not a catalog.** OpenRouter returns `usage.cost` (the real
   dollar amount charged) on every response automatically — verified against the docs; the
   old `usage:{include}` / `stream_options:{include_usage}` opt-ins are deprecated no-ops, and
   streamed usage arrives in the final SSE chunk. Read `usage.cost` and prefer it over the
   computed price, exactly as the Worker side already does in `native_usage.py`. Tokens are
   tracked regardless (OpenAI-shaped `usage`).

## Build slices

The work splits into three independently shippable changes. An operator can already reach
OpenRouter today via `openai-compatible` + a pasted key, so each slice removes one layer of
friction:

- **Slice 1 — OpenRouter provider + truthful cost.** Transport routing, base-URL default,
  provider regex, curated shortlist, frontend provider option (§1, §4, §5) — this alone gives
  "many models, one pasted key" with truthful **token** tracking for free. **Plus** the cost
  capture (§1 pricing): a shared `resolve_cost(model, response)` that prefers the response's
  `usage.cost` and falls back to `_calculate_known_cost`, updated at the ~4 Control Plane call
  sites (`tasks.py:339/909/1521`, `proxy.py:97`). Mirrors the existing Worker pattern in
  `native_usage.py:127`. Provider-agnostic, no regression for OpenAI/Anthropic (still `None`
  for unknown models). Ships truthful **tokens and dollars** together.
- **Slice 2 — OAuth "Connect" button** (§2). Removes the paste. External contract verified
  against the OpenRouter docs; buildable as written.
- **Slice 3 — searchable catalog picker** (§3). UX-only now that pricing comes from
  `usage.cost`. Optional; curated shortlist + custom-id covers function without it.

## Implementation

### 1. Transport — `src/foreman_ai_hq/llm.py`
- Route `openrouter` through the existing OpenAI-compatible path: in `acompletion`
  (`llm.py:52`) include `openrouter` in the OpenAI-shaped branch.
- In `_provider_config`, when `provider == "openrouter"` and no base URL is set, default
  `base_url` to `https://openrouter.ai/api/v1`. Add `DEFAULT_OPENROUTER_BASE_URL` next to
  the existing defaults (`llm.py:17-18`).
- Optionally send OpenRouter attribution headers (`HTTP-Referer`, `X-Title`) in
  `_openai_compatible_completion` (`llm.py:58`); not required for function.
- Pricing (**Slice 1, first-class — not deferred**): add `extract_cost(response) -> float | None`
  reading `usage.cost` (optionally `cost_details.upstream_inference_cost` as evidence), and wrap
  `calculate_cost` into `resolve_cost(model, response)` that returns the reported cost when present
  and falls back to `_calculate_known_cost` (`llm.py:316`) otherwise — its `None` fallback for
  unknown models is unchanged. Update the ~4 Control Plane call sites that today compute cost from
  tokens (`routes/tasks.py:339`, `:909`, `:1521`; `routes/proxy.py:97`) to pass the response.
  This is the same "prefer provider-reported cost" pattern already used on the Worker side
  (`native_usage.py:127`, `:250`). No catalog math involved.

### 2. OAuth PKCE flow — new routes in `src/foreman_ai_hq/routes/portal.py`
Both routes gated by `Depends(require_portal_auth)` like every other settings route.
- `GET /settings/control-plane/openrouter/oauth/start`: generate `code_verifier`
  (43–128 chars), `code_challenge = base64url(sha256(verifier))`, and a random `state`.
  Persist `{state -> verifier}` server-side with a short TTL (small SQLite table via the
  existing `db` layer, or an in-process TTL map). Redirect to
  `https://openrouter.ai/auth?callback_url={base}/settings/control-plane/openrouter/oauth/callback&code_challenge={challenge}&code_challenge_method=S256&state={state}`,
  where `{base}` is derived from the request scheme+host (localhost for `foremanctl serve`).
- `GET /settings/control-plane/openrouter/oauth/callback?code=&state=`: validate/consume
  `state`, look up the verifier, POST `https://openrouter.ai/api/v1/auth/keys` with
  `{code, code_verifier, code_challenge_method:"S256"}`, receive `{key}`. Persist the key
  via `write_control_plane_secret` under the configured env name (default
  `OPENROUTER_API_KEY`), set provider=`openrouter`, redirect back to
  `/settings/control-plane` with a success flash. **Never log `code` or the key**; apply
  the same redaction rules as the existing Portal-Managed Control Plane API Key path.
- Keep manual key paste as a fallback for headless/no-OAuth operators.

### 3. Model catalog — new endpoint in `portal.py` (Slice 3, optional UX)
- **Not needed for pricing** (cost comes from `usage.cost`, see §1). This is purely the
  searchable typeahead picker. Deferrable — the curated shortlist + custom-id fallback deliver
  full function without it.
- `GET /api/settings/control-plane/openrouter/models` (auth-gated): proxy
  `GET https://openrouter.ai/api/v1/models`, cache ~5 min, return normalized `{id, name}`.
  On fetch failure return an empty list + a flag so the UI falls back to custom-id entry.

### 4. Settings / validation plumbing
- `portal.py:213` — extend the provider regex to
  `^(openai|anthropic|openai-compatible|openrouter)$`.
- `portal.py:256` `CURATED_CONTROL_PLANE_MODELS` — add an OpenRouter "recommended for
  orchestration" shortlist (a few strong tool-use ids, e.g. `anthropic/claude-sonnet-*`,
  `openai/gpt-*`, `google/gemini-*`).
- `src/foreman_ai_hq/operator_config.py` / `settings.py` — accept provider `openrouter`,
  default `api_key_env=OPENROUTER_API_KEY`, auto-fill base URL. Reuse
  `write_control_plane_secret` / `load_operator_secrets_env`.

### 5. Frontend — `frontend/src/views/ControlPlaneSettings.jsx`
- `PROVIDERS` (`:11`): put `openrouter` first labeled "OpenRouter (recommended)"; group the
  other three under an Advanced disclosure.
- When provider is `openrouter`: render a **"Connect with OpenRouter"** button linking to the
  OAuth start route; hide the raw-key input from the primary path (keep "paste existing key"
  inside Advanced as a fallback).
- Slice 1 reuses the existing model `<select>` (`:212-223`) as-is: the OpenRouter curated
  shortlist plus the existing **custom model id** free-text fallback (`:225-240`) already
  cover it. **Slice 3** later swaps that `<select>` for a **searchable typeahead** over the
  live catalog endpoint.
- Keep the direct providers rendering exactly as today when selected.

### 6. Docs + ADR
- `CONTEXT.md`: add OpenRouter as a Control Plane provider; document the OAuth PKCE
  "Connect" flow under **Portal-Managed Control Plane API Key**; add a one-line clarifier
  that **ACP is a Worker Adapter transport, not a Control Plane option**.
- `docs/TODO.md`: leave the ACP item as a future Worker transport; link to this doc as the
  home for the Control Plane multi-model/OAuth work.
- ADR `docs/adr/0001-openrouter-oauth-control-plane-front-door.md` (written, status
  *proposed*): records why the default front door is an aggregator with OAuth rather than
  per-provider OAuth (which doesn't exist for API billing) — hard-ish to reverse, surprising
  without context, a real trade-off (churn/dependency vs. one low-friction multi-model path).

## Verification

- **Unit:** `_provider_config` resolves the OpenRouter base URL; provider regex accepts
  `openrouter`; `resolve_cost` returns the response's `usage.cost` when present and
  `None`-falls-back to `_calculate_known_cost` for a provider that reports no cost (OpenAI
  path unchanged).
- **OAuth (mocked):** state/verifier roundtrip; callback exchanges code→key, writes the
  secret, and **no test asserts the key/code appears in any log or response body**.
- **Catalog (mocked):** `/models` proxy normalizes and caches; failure yields the
  custom-id fallback path.
- **End-to-end (manual, real OpenRouter account):** `foremanctl serve` →
  `/settings/control-plane` → select OpenRouter → **Connect** → pick a model from the
  searchable catalog → **Test control-plane connection** passes → confirm the estimator/
  task-breakdown run records the spend as **Orchestration Tokens** (thesis check).
- **Regression:** point the Advanced `openai-compatible` provider at a local Ollama
  (`http://localhost:11434/v1`, dummy key) and confirm the existing flow still works.

## Explicitly out of scope
- ACP / Agent Client Protocol (separate future **Worker Adapter** transport; deferred —
  see the ACP item in `docs/TODO.md`).
- Per-provider OAuth for direct OpenAI/Anthropic API access (does not exist).
- Worker-layer auth changes (Claude Code / Codex / Gemini native sign-in already exists).
