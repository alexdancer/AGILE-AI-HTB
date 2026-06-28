## Context

The repo already has the product primitives public users need: `htb init`, `htb serve`, `htb check`, portal-managed control-plane provider/model/API-key setup, Docker local Control Plane smoke support, project workspace entry, Worker Adapter setup, and session/token evidence. The public-release gap is sequencing and trust: a first-time operator should not have to reverse-engineer which key configures the control-plane model, which auth belongs to OpenCode/Claude/Codex/Hermes, or what Docker can and cannot launch.

This change is onboarding/support polish. It should document and lightly polish the existing flow rather than introduce hosted execution, new adapters, a secret vault, or a frontend rewrite.

## Goals / Non-Goals

**Goals:**

- Give public users one README-first path that works from a fresh clone to a tiny governed launch proof.
- Make portal-managed control-plane API key setup the normal local path while preserving `.htb/secrets.env`/environment compatibility.
- Make `htb check` output useful as a redacted support artifact.
- Explain Docker as a no-secret Control Plane/Portal proof, not a host Worker Adapter bridge.
- Provide Worker Adapter setup guidance that separates adapter identity, Worker CLI auth, tracking mode, launch readiness, and common failures.
- Add release hygiene docs/templates with no new dependencies.

**Non-Goals:**

- No hosted sandbox, split runner, OAuth, multi-user permissions, or secret vault.
- No new Worker Adapter execution behavior or tracking-mode semantics.
- No changes to provider clients, token accounting, budget guardrails, or board lifecycle.
- No SPA, screenshot automation framework, or docs site generator.

## Decisions

### README owns the first-run path

The README should be the public entrypoint and should present one path: install, `htb init`, `htb serve`, login, configure `/settings/control-plane`, test connection, connect a project, configure Worker Adapter, and launch a tiny proof. Deeper docs can expand each step, but the README should not make users pick among several startup stories.

Alternative considered: add a separate quickstart doc only. Rejected because public users and GitHub visitors start in README.

### Portal-managed key is normal; env/secrets file remains compatibility

The onboarding path should say that normal local operators paste the control-plane API key in `/settings/control-plane`. It should still document that the portal writes to ignored `.htb/secrets.env`, blank submits preserve existing secrets, and environment variables can override saved config.

Alternative considered: return to manual `.htb/secrets.env` editing in docs. Rejected because the completed portal-managed key change exists specifically to reduce that friction.

### Support output stays text-first and redacted

`htb check` should remain a small text command using PASS/WARN/FAIL lines. Public issue templates should ask for redacted `htb check` output, OS/install method, control-plane provider, Worker Adapter, tracking mode, and whether the key was configured through portal or env. Do not add telemetry or log upload.

Alternative considered: build a diagnostic bundle generator. Rejected until support volume proves the text output insufficient.

### Worker Adapter matrix is documentation, not new adapter logic

The public matrix should explain OpenCode, Claude Code, Codex, and Hermes in terms of adapter identity, Worker CLI auth source, supported tracking modes, launchable evidence, and common failure. It must not imply that the control-plane API key configures native Worker CLIs.

Alternative considered: redesign Worker Setup UI before public release. Rejected; the existing guided setup already has the core workflow.

### Release hygiene uses plain repository files

Add normal repository files/templates first: license, security guidance, contributing guidance, issue templates, and a redacted support checklist. Avoid a docs framework, generated site, or governance process docs beyond what a public repo needs.

Alternative considered: publish a full documentation site first. Rejected as slower and unnecessary for initial release.

## Risks / Trade-offs

- Docs drift from implementation → keep the first-run path executable and back it with existing CLI/portal tests where copy changes affect behavior.
- Users paste secrets into issues → issue templates and support checklist explicitly require redaction and say secrets are never needed for triage.
- Docker users expect host Worker launches → repeat the Docker boundary in README, Docker docs, and trust-boundary docs.
- Onboarding gets too long → README keeps the happy path; detailed trust/matrix/support docs link out.
