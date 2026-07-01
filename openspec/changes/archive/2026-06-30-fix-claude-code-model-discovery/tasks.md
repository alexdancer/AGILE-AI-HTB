## 1. Regression Coverage

- [x] 1.1 Add a failing test showing Claude Code model discovery does not execute `claude models` and returns the curated Claude inventory.
- [x] 1.2 Add a parser regression test where successful prose stdout is rejected as Worker model inventory.
- [x] 1.3 Add or update Worker Setup route tests showing adapter-scoped POST actions redirect back with `adapter_id` preserved.

## 2. Curated Claude Code Inventory

- [x] 2.1 Update the Claude Code seeded/supported model list to exactly `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, and `claude-haiku-4-5`.
- [x] 2.2 Make Claude Code discovery return curated discovery evidence without launching a Claude subprocess.
- [x] 2.3 Ensure curated discovery refreshes Claude Code inventory without silently expanding the operator-approved allowed subset.

## 3. Discovery Parser Hardening

- [x] 3.1 Restrict plain-line discovery parsing to valid model-id-shaped lines.
- [x] 3.2 Keep OpenCode native `opencode models` discovery working for valid line-oriented output.
- [x] 3.3 Ensure stale prose discovery evidence is not rendered as current Claude Code allowed-model choices after curated discovery runs.

## 4. Worker Setup Context

- [x] 4.1 Preserve `adapter_id` in redirects after discover, allowed-model save, verification, and diagnostics actions.
- [x] 4.2 Verify Worker Setup renders the acted-on adapter after those actions.

## 5. Verification

- [x] 5.1 Run targeted worker adapter and portal tests covering discovery, allowed-model saves, and Worker Setup redirects.
- [x] 5.2 Run `openspec validate fix-claude-code-model-discovery --strict`.
- [x] 5.3 Run the repo test command `uv run pytest`.
