## Context

Task Breakdown Agent calls use the control-plane/orchestrator model, not Worker Adapter models. The current direct Anthropic path is reachable, but the small DEMO 2099 Markdown intake produced a complete answer only when the Task Breakdown completion cap was raised above the current 4,096-token bound.

Live evidence from the failing source:
- 4,096 cap: `finish_reason=max_tokens`, incomplete fenced JSON, validation failure.
- 8,192 cap: `finish_reason=end_turn`, 7,268 completion tokens, valid Proposed Task Breakdown with five candidates.

## Goals / Non-Goals

**Goals:**
- Give Task Breakdown Agent enough bounded output headroom for realistic small-demo Markdown intake.
- Keep strict output validation and manual recovery for malformed or truncated output.
- Keep the change local to Task Breakdown Agent request sizing and tests.

**Non-Goals:**
- No global provider default change.
- No Worker Adapter, Worker model discovery, launch, proxy, or token-accounting change.
- No retry loop, JSON repair parser, deterministic Markdown fallback, or prompt rewrite.
- No schema migration or Portal UI change.

## Decisions

- Set the Task Breakdown Agent completion cap to 16,384 tokens.
  - Rationale: 8,192 left only about 12.7% headroom over the observed 7,268-token small-demo answer. 16,384 is a boring bounded ceiling with room for modest variation.
  - Alternative rejected: 8,192 is likely to fail again on slightly more verbose candidates.
  - Alternative rejected: 32,768+ makes runaway verbose breakdowns easier and is unnecessary until evidence shows 16,384 is insufficient.

- Keep the cap as a task-breakdown-scoped constant.
  - Rationale: estimation, review, reports, and connection tests do not need larger outputs for this bug.
  - Alternative rejected: raising the Anthropic/provider default would broaden cost/risk without fixing a wider proven issue.

- Preserve strict parser behavior.
  - Rationale: the failure mode should remain explicit manual recovery when output is malformed, incomplete, or schema-invalid.
  - Alternative rejected: extracting arbitrary JSON from prose or repairing partial JSON would hide provider failures and can create unsafe task cards.

## Risks / Trade-offs

- Larger cap can allow larger control-plane spend if Claude becomes verbose → bounded at 16,384 and scoped only to Task Breakdown Agent calls.
- Some future large imports may still exceed 16,384 → keep failure/manual recovery; revisit with prompt compression or dynamic caps only if real evidence demands it.
