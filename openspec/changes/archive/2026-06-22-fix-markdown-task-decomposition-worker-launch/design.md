## Context

The board estimator currently accepts pasted markdown and uploaded `.md` files, but the intake route treats the normalized markdown as one task description. The helper that detects markdown breakdown items only records metadata on that single card, so a multi-task demo file becomes one oversized Estimated card and the control-plane estimator sees the full document for one estimate.

Worker model recommendation is constrained to discovered Worker Adapter models, but when the control-plane estimator recommends a model name that does not exactly exist in the selected adapter inventory, the current constraint path can choose the first discovered model. On OpenCode installations where `opencode models` returns `opencode/big-pickle` first, simple tasks can be routed to that heavyweight model.

OpenCode launch currently uses a preset launch template equivalent to `opencode`, which starts the CLI without the non-interactive `run` subcommand, selected model, JSON output mode, or task prompt. That creates a recoverable Worker Run failure class such as `Worker adapter launch failed. Return code: 1` even when the adapter and model inventory are otherwise present.

The design preserves the agent-harness model split: the control-plane/orchestrator model performs estimation, decomposition, routing, and review; Worker/coding harness models are launched through local Worker Adapters such as OpenCode. Tracking mode remains a separate usage-authority state (`proxy_governed`, `native_usage`, `observed_only`).

## Goals / Non-Goals

**Goals:**

- Convert deterministic markdown task lists into multiple task rows/cards at intake time.
- Estimate each created card independently from scoped task text rather than from the whole markdown file.
- Preserve enough source metadata to trace every generated card back to its uploaded/pasted markdown source.
- Route recommendations to appropriate discovered Worker models without blindly using discovery order.
- Launch OpenCode via a non-interactive command that includes the selected model and prompt.
- Add regression tests that fail on the diagnosed one-card import, `opencode/big-pickle` fallback, and bare `opencode` launch command.

**Non-Goals:**

- No new Worker Adapter abstraction or generic provider-key adapter.
- No change to the meaning of `proxy_governed`, `native_usage`, or `observed_only` tracking.
- No requirement that every markdown heading becomes a card; decomposition should be deterministic and conservative.
- No attempt to prove token savings from decomposition beyond ensuring per-card scoped estimation.
- No new external markdown parsing dependency unless existing simple parsing proves insufficient.

## Decisions

### 1. Decompose deterministic task items before estimation

The intake route will normalize the selected markdown source, extract deterministic task items, and create one estimate/task per extracted item when two or more items are found. Checklist items (`- [ ]`, `* [ ]`) and explicit task/phase bullets are good initial boundaries because they are stable and visible in demo files. If fewer than two items are found, the route keeps the current single-card flow.

Alternative considered: keep one database task and render `task_breakdown` metadata as pseudo-cards in the board UI. Rejected because launch, estimate, model recommendation, task lifecycle, Worker Run records, and review actions all operate on persisted task rows.

### 2. Preserve markdown source context without re-estimating the whole file per card

Each generated card will receive a scoped description built from the item text plus minimal parent heading/context when useful. Metadata will record `intake_source`, `intake_filename` for uploads, a parent source identifier/hash, `decomposition_index`, `decomposition_count`, and the original item text. The control-plane estimator request for each card must not include the entire original markdown document as the task body.

Alternative considered: include the full source markdown on every card for context. Rejected because it recreates the inflated estimate problem and can multiply context cost across all cards.

### 3. Choose discovered Worker models by intent/size instead of inventory order

When the estimator recommendation is not present in the selected adapter inventory, the constraint logic will rank available discovered models by task estimate/complexity and model-name signals. Small/simple work should prefer lightweight discovered models (`haiku`, `mini`, `nano`, `flash`) when available. Heavier names (`big-pickle`, `opus`, `pro`, `max`, high-variant style names) should be reserved for large/complex work or used only when no smaller compatible discovered model exists.

Alternative considered: hard-code `opencode/gpt-5.4-mini` as the fallback. Rejected because discovered model inventories vary by installation and adapter; the harness should select from what was actually discovered.

### 4. Fix OpenCode defaults at the adapter preset/builder boundary

OpenCode presets and command planning should produce non-interactive launch commands equivalent to:

`opencode run --model {model} --format json {prompt}`

The selected model remains the Worker model, not the control-plane estimator model. For `proxy_governed`, the command environment continues to route model calls through the Harness Proxy. For `native_usage`, the native launch command still requires machine-readable usage evidence before it is budget-authoritative.

Alternative considered: rely on user configuration to override the broken template. Rejected because the default preset should work for the supported OpenCode Worker Adapter path and the current default is a known footgun.

## Risks / Trade-offs

- Deterministic markdown parsing may miss non-checklist prose tasks → keep fallback single-card behavior and preserve source metadata for manual correction.
- Creating several estimates can spend more control-plane estimation tokens than one large estimate → each estimate is smaller/scoped, and tests should assert the whole markdown is not repeated per card.
- Model-name ranking is heuristic → keep the selected model and constraint reason in metadata so operators can override or diagnose routing.
- Existing databases may already have OpenCode adapter rows with the old bare launch template → implementation may need a migration/normalization path or command-builder fallback that fixes known-bad bare OpenCode templates at launch time.
- OpenCode CLI flags can change → tests should cover the command shape based on currently verified `opencode run --help`, and failure evidence should remain sanitized if command execution fails.
