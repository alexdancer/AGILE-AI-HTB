## Why

AGILE-AI-HTB is close to public release, but a new operator still has to infer too much from architecture docs, environment-variable tables, and demo notes. Public users need one trustworthy first-run path that proves the Portal, control-plane model setup, project connection, Worker Adapter readiness, and token-evidence loop without confusing control-plane credentials with Worker CLI auth.

## What Changes

- Add a README-first public onboarding path for the first 10 minutes: install, `htb init`, `htb serve`, login, `/settings/control-plane` provider/model/API-key entry, explicit connection test, project connect, Worker setup, and tiny launch proof.
- Add public trust-boundary documentation covering what AGILE-AI-HTB does and does not govern, where local secrets are stored, and why Worker Adapter auth remains separate from the control-plane API key.
- Align `htb check` and support guidance with the portal-managed control-plane API key flow, including actionable PASS/WARN/FAIL remediation text.
- Add a Worker Adapter setup matrix for OpenCode, Claude Code, Codex, and Hermes that separates adapter identity from `proxy_governed`, `native_usage`, and `observed_only` tracking modes.
- Clarify the no-secret Docker path as a Control Plane/Portal smoke proof, not host-native Worker Adapter launch readiness.
- Add public release hygiene docs/templates: license, security/contact guidance, contributing guidance, issue template inputs, and redacted setup-support checklist.
- Add a small screenshots/GIF checklist for setup, board launch, and session report/token evidence.

## Capabilities

### New Capabilities
- `public-release-onboarding`: public-facing onboarding, trust-boundary, support, and release-hygiene requirements for first-time operators.

### Modified Capabilities
- `operator-setup`: `htb check` and setup docs must point normal local users to portal-managed control-plane API key setup while preserving CLI/env compatibility.
- `docker-local-run`: Docker docs must frame the no-secret path as Control Plane/Portal readiness and explicitly exclude host-native Worker Adapter readiness.
- `guided-worker-setup`: Worker setup docs must present adapter identity, Worker CLI auth, tracking mode, launchable evidence, and common failure modes separately.

## Impact

- Affected docs: `README.md`, `docs/`, release/support templates, screenshots or recorded media paths.
- Affected CLI/UI copy: `htb check` output and setup/support wording only; no new dependencies or hosted infrastructure.
- Affected tests: documentation/link checks if present, CLI output tests for changed `htb check` remediation, and existing portal/setup tests for onboarding copy.
- No changes to Worker Adapter execution semantics, provider clients, secret storage model, or launch guardrails.
