## Context

The Control Plane model connection today supports `openai`, `anthropic`, and
`openai-compatible`, validated by a provider regex (`routes/portal.py:213`) and rendered from a
single authoritative curated list `CURATED_CONTROL_PLANE_MODELS` (`routes/portal.py:256`).
Requests run through `LLMClient.acompletion` (`llm.py:50`), which routes `{openai,
openai-compatible}` to `_openai_compatible_completion` and `anthropic` to its own path.
Usage is read by `extract_usage` (`llm.py:97`, OpenAI-shaped `usage`), and cost is computed
separately by `calculate_cost` → `_calculate_known_cost` (`llm.py:316`), a hard-coded 3-model
price table returning `None` for anything else.

OpenRouter is an OpenAI-compatible aggregator. Verified against its docs: the API returns an
OpenAI-shaped `usage` object that also carries `cost` (real dollars charged) on every response
automatically — the old `usage:{include}` / `stream_options:{include_usage}` opt-ins are
deprecated no-ops, and for streaming the usage arrives in the final SSE chunk. The Worker side
already prefers a provider-reported cost over a computed one (`native_usage.py:127`, `:250`);
the Control Plane side never did, because until OpenRouter no Control Plane provider reported
cost.

## Goals / Non-Goals

**Goals:**
- Accept `openrouter` as a Control Plane provider using the existing OpenAI-compatible transport
  (no new client), with a sensible default base URL, key env name, and curated shortlist.
- Make cost accounting prefer the response's `usage.cost` when present, while preserving token
  accounting and known-model fallback behavior for existing providers.
- Keep the operator flow to "paste one OpenRouter key" — no OAuth, no catalog, this slice.

**Non-Goals:**
- OAuth PKCE "Connect" button (Slice 2).
- Searchable live `/models` catalog picker (Slice 3) — pricing no longer needs it.
- Any change to Worker Adapters, token counting, direct provider transport behavior, or database
  schema beyond making `token_turns.cost` nullable. Proxy-governed Worker turns share that ledger
  and therefore inherit nullable unresolved-cost persistence.

## Decisions

**1. OpenRouter reuses the OpenAI-compatible path — one token, not a new branch.**
Add `openrouter` to the OpenAI-compatible provider set in `acompletion`, and add an
`openrouter` → `https://openrouter.ai/api/v1` default in `_provider_base_url`. OpenRouter speaks
the OpenAI chat-completions contract, so nothing else in the transport changes. Attribution
headers (`HTTP-Referer`/`X-Title`) are optional and skipped this slice.

**2. Cost is captured at a single shared seam: `resolve_cost(model, response)`.**
Add `extract_cost(response) -> float | None` reading `usage.cost` (with `cost_details` available
as evidence but not required). Wrap the existing cost path in
`resolve_cost(model, response)` that returns the reported cost when present, else
`_calculate_known_cost(model, prompt, completion)`. The three Control Plane orchestration call
sites (`routes/tasks.py:339`, `:909`, `:1521`) and the proxy-governed Worker accounting seam
(`routes/proxy.py:97`) already hold the full response, so they switch from
`calculate_cost(model, p, c)` to `resolve_cost(model, response)`. This is
the root-cause fix in the shared function rather than a per-caller patch, and it mirrors the
established Worker-side pattern. `extract_usage` is left as-is (tokens only); cost travels
separately, so its return shape does not change. Call sites persist the resolver result without
coercing `None` to `0.0`; `token_turns.cost` becomes nullable through an idempotent migration so
unknown cost remains distinct from a genuinely free call.

**3. Existing-provider token and known-model pricing behavior stays stable.**
OpenAI/Anthropic responses carry no `cost`, so `resolve_cost` falls through to
`_calculate_known_cost`, preserving existing computed prices for known models. The token path is
untouched for every provider. Unpriced calls intentionally change at persistence: task and
proxy-governed Worker call sites now store database `null` instead of coercing `None` to legacy
`0.0`. Existing numeric ledger values remain unchanged.

**4. Settings/config: additive.**
Widen the provider regex to `^(openai|anthropic|openai-compatible|openrouter)$`, add an
OpenRouter shortlist to `CURATED_CONTROL_PLANE_MODELS`, and teach `operator_config.py`/
`settings.py` to accept `openrouter` with default `api_key_env=OPENROUTER_API_KEY` and the
auto base URL. The frontend adds `openrouter` to `PROVIDERS` and reuses the existing curated
`<select>` + custom-id fallback — no picker rewrite.

**5. Cost is made visible at the connection-test panel — the first control-plane cost surface.**
Today every cost display is Worker-side (`Dashboard.jsx:130`, `Board.jsx:313`,
`SessionReport.jsx:126`), and the control-plane test handler (`portal.py:1326`) records
`extract_usage(response)` (tokens only). So a captured control-plane cost would be invisible. We
add the resolved cost to the test evidence (call `resolve_cost` in the test handler) and render a
Cost line beside the existing "Total tokens" in `ControlPlaneSettings.jsx` (`~:364`). Unavailable
cost (provider reports none and model unpriced) renders as an explicit "unavailable" label, never
`$0.00`. This keeps the surface minimal — the operator sees the dollar cost exactly where they set
OpenRouter up. A broader dashboard "orchestration spend" figure is deferred (out of scope).

## Risks / Trade-offs

- **Streaming usage:** OpenAI-compatible streaming omits usage unless the provider emits a final
  usage chunk; OpenRouter emits it automatically, and `final_stream_usage` (`llm.py:322`) already
  reads the last chunk that carries values. If a Control Plane path streams and counts appear
  zero, that is the pre-existing OpenAI-compatible behavior, not an OpenRouter regression.
  Control Plane estimator/breakdown calls are non-streaming JSON, so this is expected to be moot.
- **Cost provenance:** `usage.cost` is OpenRouter's charged amount (may include its margin);
  `cost_details.upstream_inference_cost` is the upstream figure. We record the charged `cost` as
  the truthful spend. Acceptable — it is what the operator actually pays.
- **Curated shortlist drift:** OpenRouter model IDs change over time. The shortlist is a
  convenience; the custom-id path covers anything not listed, so a stale shortlist degrades to
  "type the id," not breakage.
- **`usage.cost` shape trust:** if a future OpenRouter response omits `cost`, `resolve_cost`
  simply falls back — no crash, no wrong number.
