## 1. Public Onboarding Docs

- [x] 1.1 Rewrite the README quickstart into a first-10-minutes path: install, `htb init`, `htb serve`, login, `/settings/control-plane`, save/test control-plane connection, connect project, Worker setup, tiny launch proof.
- [x] 1.2 Add or update a trust-boundary doc explaining Control Plane vs Execution Plane, portal-managed local secret storage, Worker CLI auth separation, tracking modes, and Docker/local-runner limits.
- [x] 1.3 Add a public visual proof checklist and placeholder paths for setup, project/board launch readiness, and session report/token evidence screenshots or a short recording.

## 2. Support and Release Hygiene

- [x] 2.1 Add `LICENSE`, `SECURITY.md`, and `CONTRIBUTING.md` with concise public-repo guidance.
- [x] 2.2 Add GitHub issue templates for setup/support and bug reports that request redacted `htb check`, OS, install method, control-plane provider, Worker Adapter identity, tracking mode, and key configuration path.
- [x] 2.3 Add a redacted setup-support checklist that explicitly says not to paste API keys, portal tokens, `.htb/secrets.env`, or raw credentials.

## 3. Operator Setup and Docker Guidance

- [x] 3.1 Update `htb check` remediation text so missing control-plane API key guidance points to `/settings/control-plane`, ignored `.htb/secrets.env`, or env vars, and never implies Worker CLI auth is configured by the control-plane key.
- [x] 3.2 Update or add CLI tests for the changed `htb check` PASS/WARN/FAIL output and redaction expectations.
- [x] 3.3 Update Docker docs so the no-secret path proves Control Plane/Portal startup and persistence, while real provider tests and Worker verification are clearly later credential-dependent steps.

## 4. Worker Adapter Public Guidance

- [x] 4.1 Add a Worker Adapter setup matrix for OpenCode, Claude Code, Codex, and Hermes covering Worker CLI auth source, tracking modes, launchable evidence, and common failure modes.
- [x] 4.2 Ensure Worker setup docs and portal copy preserve adapter identity vs tracking mode: `proxy_governed`, `native_usage`, and `observed_only` are tracking modes, not adapter names.
- [x] 4.3 Verify the docs state `observed_only` is diagnostic-only and not normal AGILE Board launchable.

## 5. Verification

- [x] 5.1 Run `openspec validate prepare-public-release-onboarding --strict`.
- [x] 5.2 Run focused tests for touched CLI/docs/portal setup behavior.
- [x] 5.3 Run `uv run pytest` after implementation edits.
