## Why

Claude Code Worker model discovery currently assumes `claude models` is a native model-list command. On the installed Claude Code CLI, that command is treated as an AI prompt, so prose can be parsed and displayed as selectable Worker models.

## What Changes

- Stop treating Claude Code as a native model-discovery CLI.
- Use a curated Claude Code Worker model inventory instead:
  - `claude-opus-4-8`
  - `claude-opus-4-7`
  - `claude-opus-4-6`
  - `claude-sonnet-4-6`
  - `claude-haiku-4-5`
- Keep OpenCode native discovery through `opencode models` unchanged.
- Reject prose, Markdown, and other non-model-id stdout as discovered Worker model IDs.
- Preserve the selected Worker Adapter context after discovery/configuration actions so the operator returns to the adapter they acted on.
- Preserve the distinction between Claude Code model inventory and Claude Code `native_usage` proof; native verification still uses `claude -p --model ... --output-format json|stream-json --verbose`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-worker-model-discovery`: Claude Code uses a curated model inventory instead of running `claude models`, and model discovery parsing rejects prose as model IDs.
- `worker-adapter-verification`: Claude Code native verification can use curated Claude model IDs and remains separate from model discovery.
- `guided-worker-setup`: Worker Setup actions return to the active adapter context and show curated Claude models as explicit/curated Worker model choices.

## Impact

- Affected code: Worker adapter discovery, seeded/curated Worker model allowlists, Worker Setup redirects/view models, and model parsing tests.
- No database schema change expected; reuse existing adapter config/discovery evidence and supported/allowed model fields.
- No new dependencies.
- No changes to control-plane/orchestrator model settings or provider credentials.
