## Context

The Control Plane model connection check is a reachability smoke test: it sends a tiny request and records sanitized success/failure evidence. Task Breakdown is a heavier control-plane/orchestrator call: it sends the source text, slicing instructions, optional repo context, requests strict Proposed Task Breakdown JSON, and currently allows a large completion budget.

Recent local evidence showed two distinct failure classes for the same Task Breakdown source:

```text
Control Plane test
  tiny prompt, ~64 total tokens
  ✅ provider reachable

Task Breakdown Agent
  source_text ~= 12,770 chars
  temperature: 0
  max_tokens: 16,384
  non-streaming direct provider request
  ❌ exposes provider parameter compatibility and timeout behavior
```

For Anthropic, the current adapter translates OpenAI-shaped control-plane requests to the Anthropic Messages API. Model-by-model temperature filtering is brittle: `claude-sonnet-5` was fixed, but `claude-opus-4-8` still failed with the same `temperature is deprecated for this model` HTTP 400. The adapter should stop sending that OpenAI-style parameter to Anthropic at all.

The Sonnet 5 timeout is a separate class: once `temperature` is removed, the request reaches the provider but can exceed the current local read timeout before a complete response is available.

## Goals / Non-Goals

**Goals:**

- Make Anthropic request translation provider-compatible by omitting `temperature` for every Anthropic Messages API call.
- Preserve OpenAI and OpenAI-compatible request behavior.
- Keep Task Breakdown Model work in the control-plane/orchestrator layer, separate from Worker Adapter models and launches.
- Make Task Breakdown timeout failures safe and actionable by reporting model, timeout seconds, source size, and output budget.
- Keep the existing failed-breakdown/manual-recovery lifecycle.
- Add deterministic tests for Anthropic request translation and timeout diagnostics.

**Non-Goals:**

- No Worker Adapter changes.
- No Control Plane model picker redesign.
- No Anthropic model discovery.
- No streaming Task Breakdown implementation.
- No retry/repair parser or deterministic Markdown fallback.
- No prompt/source text or secret values in diagnostics.

## Decisions

### 1. Omit `temperature` for all Anthropic requests

The Anthropic adapter SHALL not copy `request["temperature"]` into Anthropic Messages payloads, regardless of model ID.

Rationale: The Harness sends OpenAI-shaped internal requests for convenience, but Anthropic request translation is the compatibility boundary. A model prefix denylist already missed `claude-opus-4-8`; omitting the parameter for the provider avoids future stale-model failures.

Alternatives considered:

- Extend the denylist with `claude-opus-4-8`. Rejected because it preserves whack-a-mole behavior.
- Keep temperature for older Claude models. Rejected because control-plane planning calls value compatibility and deterministic prompts more than a provider knob that current models reject.

### 2. Keep output budget high but explicit for Task Breakdown

The existing Task Breakdown cap of 16,384 completion tokens remains valid for structured breakdown JSON. This slice should not lower the cap by default because prior Anthropic Task Breakdown evidence required a large enough completion budget for real Proposed Task Breakdown objects.

Instead, the cap should be explicit in code/tests/diagnostics so operators can see the request scale when failures happen.

Alternatives considered:

- Lower the cap to 4,096 or 8,192. Deferred because it could reintroduce truncation/invalid JSON failures for medium demo tasks.
- Dynamically retry with larger caps. Deferred because this slice is about compatibility and diagnostics, not repair/retry orchestration.

### 3. Add Task Breakdown-specific timeout diagnostics

The LLM/client layer may keep a generic request timeout, but Task Breakdown failures should preserve enough context to explain why a reachable model failed the heavier breakdown path.

A safe timeout diagnostic should include:

- provider/model identity
- timeout seconds
- source character length
- max output tokens
- no API key values
- no raw source text/prompt body

Alternatives considered:

- Only increase the generic timeout. Rejected as insufficient because it hides why the path differs from model verification.
- Store full request payload for debugging. Rejected because it risks source/prompt leakage and unnecessary persistence.

### 4. Keep failure recovery unchanged

Timeouts and provider HTTP errors still create breakdown-failed/manual recovery state. The operator can retry, create a manual candidate, or cancel.

Rationale: This preserves the existing lifecycle contract: no silent Markdown splitting and no oversized whole-source task creation.

## Risks / Trade-offs

- Older Anthropic models that accepted `temperature` will stop receiving it → Acceptable because these are control-plane calls and prompt/schema should carry deterministic behavior.
- Longer Task Breakdown timeout could make the UI wait longer → Mitigate by making timeout explicit and surfacing clear failure diagnostics; streaming/progress can be a later change.
- Keeping 16,384 max output tokens can still be slow/costly → Mitigate by showing output budget in diagnostics and leaving splitting/retry optimization to a later evidence-backed change.
- Sanitized diagnostics may omit detail useful for debugging → Mitigate by preserving provider HTTP body/request ID when safe, while never storing secrets or source text.
