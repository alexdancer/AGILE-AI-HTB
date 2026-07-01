## Context

Worker Adapter setup separates the control-plane/orchestrator model from Worker/coding harness models. OpenCode has a usable native model-list path (`opencode models`), but Claude Code does not expose a reliable `claude models` inventory command in this environment: `claude models` is interpreted as a prompt and can return prose.

Current discovery parsing has a permissive plain-line fallback. That is useful for line-oriented CLIs such as OpenCode, but unsafe when the command output is AI-generated text.

## Goals / Non-Goals

**Goals:**

- Make Claude Code model inventory deterministic and curated.
- Stop executing `claude models` during Claude Code discovery.
- Prevent prose, Markdown, and error text from being persisted as discovered Worker model IDs.
- Keep OpenCode native model discovery working.
- Keep Claude Code `native_usage` verification and launch accounting separate from model discovery.
- Preserve the active adapter UI context after Worker Setup actions.

**Non-Goals:**

- No YAML/JSON operator-editable model inventory file in this slice.
- No database schema change.
- No control-plane model/provider setting changes.
- No proxy-governed Claude Code support.
- No new Worker Adapter families.

## Decisions

### Use the existing preset/allowlist path for curated Claude models

Set the Claude Code curated inventory in the existing seeded Worker model structures rather than adding a new config file:

```text
claude-opus-4-8
claude-opus-4-7
claude-opus-4-6
claude-sonnet-4-6
claude-haiku-4-5
```

Rationale: the app already has seeded/supported model storage and allowed-model selection. A new YAML/JSON file would add loading, packaging, override, and migration behavior without solving the bug better.

Alternative considered: add a standalone model inventory file. Rejected for this slice because non-dev operator editing is not required yet.

### Treat Claude Code discovery as curated, not native

Claude Code discovery should produce curated model evidence without launching a Claude subprocess. Native usage proof remains a separate verification path using `claude -p --model ... --output-format json|stream-json --verbose`.

Alternative considered: discover through `claude models`. Rejected because the local CLI treats `models` as a prompt.

### Harden plain-line discovery parsing

Plain-line parsing should only accept model-id-shaped lines and reject obvious prose/Markdown. This keeps OpenCode line output working while preventing AI responses from becoming checkboxes.

Alternative considered: disable plain-line parsing globally. Rejected because some OpenCode installs emit line-oriented model IDs rather than JSON.

### Preserve Worker Setup adapter context after POST actions

Worker Setup POST routes should redirect back to `/settings/workers?adapter_id={adapter_id}` after configure/discover/allowed-models/verify/diagnostics actions.

Alternative considered: split every adapter into a dedicated page. Rejected as larger UI work; preserving context fixes the confusion with less code.

## Risks / Trade-offs

- Curated Claude list may become stale → keep it small, current, and covered by tests so updates are obvious.
- `claude-haiku-4-5` is a short alias rather than the dated canonical ID → accepted because the operator requested the date-free value; native verification will prove whether the local Claude Code CLI accepts it.
- Model-id validation may reject an unusual future CLI output format → JSON discovery remains supported, and explicit configured discovery templates can still be added later if needed.
- Existing databases may retain bad prose in `config.model_discovery.models` → implementation should overwrite Claude Code discovery evidence with curated models on the next discovery action and avoid using stale prose as the current discovered list.
