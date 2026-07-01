## 1. Curated Control Plane Model Choices

- [x] 1.1 Update `src/agile_ai_htb/templates/control_plane.html` curated model list to replace stale/provider-prefixed Anthropic IDs with direct Anthropic `claude-*` IDs.
- [x] 1.2 Keep the Anthropic preset on the cheap/default `claude-haiku-4-5` path and preserve OpenAI/OpenAI-compatible behavior.
- [x] 1.3 Verify saved non-curated models still render through the Custom model path instead of being rewritten.

## 2. Tests

- [x] 2.1 Update Control Plane portal tests to assert the refreshed Anthropic options appear.
- [x] 2.2 Add or update assertions that curated Anthropic options do not include `anthropic/...` provider-prefixed IDs.
- [x] 2.3 Update connection-test fixtures that currently expect the stale Anthropic Sonnet ID.

## 3. Verification

- [x] 3.1 Run targeted Control Plane portal tests for model settings.
- [x] 3.2 Run `openspec validate refresh-control-plane-anthropic-models --strict`.
- [x] 3.3 Run `uv run pytest` after implementation, unless blocked by unrelated dirty-worktree failures and reported with evidence.
