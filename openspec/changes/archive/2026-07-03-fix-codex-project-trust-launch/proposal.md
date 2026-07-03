## Why

Codex can verify as `native_usage`, but a real AGILE Board launch can immediately fail in the task-bound connected project with `Not inside a trusted directory and --skip-git-repo-check was not specified.` The Harness already owns project binding, launch guardrails, retry state, and evidence; Codex launch should use the supported non-interactive CLI flags needed to run under that Harness-controlled context instead of relying on Codex's implicit git/trust preflight.

## What Changes

- Update Codex governed Worker launch command construction to pass the task-bound connected project root explicitly and include Codex's supported `--skip-git-repo-check` flag.
- Keep existing Harness guardrails for write-capable tasks: non-git or dirty write tasks must still be blocked before any Codex process starts.
- Keep Codex launch in native usage mode using `codex exec --json -m {model}` and `turn.completed.usage` evidence; do not change tracking authority or model allow-list semantics.
- Record the effective Codex command plan with secrets redacted, including the project root/cwd and skip-git-repo-check flag.
- Add regression tests proving Codex launch command construction no longer fails the known project-trust preflight shape while preserving model allow-list and write guardrails.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `governed-worker-launch`: Codex native usage launches must include explicit Codex project-root and git-repo-check bypass flags while preserving Harness-owned launch guardrails and native usage evidence requirements.
- `worker-adapter-verification`: Codex native usage verification command planning may use the same supported Codex git-repo-check bypass when verification runs outside a trusted git workspace, without weakening token-evidence requirements.

## Impact

- Affected backend code: Codex Worker Adapter command builder, launch command plan/evidence shaping, and verification command plan where shared.
- Affected tests: Codex adapter command construction, governed launch guardrails, native usage verification, and retryable failure evidence tests.
- No database schema change.
- No dependency change.
- No change to OpenCode, Claude Code, control-plane provider settings, token normalization, or Worker model inventory/allow-list behavior.
