# Changelog

All notable changes to AGILE-AI-HTB will be documented in this file.

## 0.1.0 - 2026-07-03

Initial public source release.

### Supported today

- Local all-in-one Portal / Control Plane launched with the `htb` operator CLI.
- Public install path from GitHub using `pipx` or the curl bootstrapper before PyPI release.
- Repo-local `.htb/` initialization for non-secret config, ignored secret storage, default guardrails, and SQLite state.
- Portal-guided control-plane model setup, project connection, Worker Adapter setup, task estimation, governed launch, token evidence, alarms, and human review.
- Worker Adapter model/auth separation from Control Plane model/auth.
- Synthetic/public-safe screenshots and demo data conventions.

### Verification for this release line

- Full Python test suite with fake LLM clients.
- Disposable pipx install smoke for `htb --help` and `htb init`.
- Package build for source distribution and wheel.
- Docker compose configuration and optional Docker smoke script for maintainers.

### Known limits

- The main supported path is local all-in-one mode.
- Worker launch readiness depends on local repository access, git state, installed Worker CLIs, and native CLI auth/config.
- Docker packages the Portal / Control Plane but does not automatically provide host Worker CLIs, local repo paths, or host credentials.
- Homebrew, hosted workspaces, fuller CLI management commands, MCP access, and PyPI install are planned/future paths until explicitly released.
