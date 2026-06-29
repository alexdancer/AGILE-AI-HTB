## Context

AGILE-AI-HTB already declares a Python console script named `htb` in `pyproject.toml`, and the CLI entry point supports `init`, `serve`, `check`, and `seed-demo`. The current public docs still lean on repo-local `uv run htb ...`, which is correct for contributors but poor for operators who expect an installed command.

The distribution design should keep AGILE-AI-HTB as a Python CLI package. npm is unnecessary unless a future audience specifically asks for npm distribution. The implementation must preserve the existing operator setup boundary: `htb init` writes non-secret local config and ignored local secret placeholders; installed CLI distribution does not change Control Plane vs Worker Adapter auth semantics.

## Goals / Non-Goals

**Goals:**
- Make the supported operator path install-once, then run bare `htb init`, `htb serve`, and `htb check`.
- Support `pipx` as the primary Python-native CLI installer.
- Provide a `curl` installer that chooses `uv tool` or `pipx`, verifies the installed `htb` command, and prints next steps.
- Prepare Homebrew installation documentation/scaffolding for macOS users.
- Keep contributor/dev instructions available for repo-local workflows and tests.

**Non-Goals:**
- Do not introduce npm as a required distribution channel.
- Do not bundle Worker Adapter CLIs such as OpenCode, Claude Code, Codex, or Hermes.
- Do not change the `htb init`/`serve`/`check` product behavior except where needed to verify installability.
- Do not require Docker, Postgres, Redis, or hosted infrastructure for the local CLI install path.

## Decisions

### Decision: Treat `pipx` as the primary public Python install path

`pipx` installs Python CLI apps into isolated environments and exposes their console scripts on `PATH`, matching the desired `htb init` UX. Before PyPI publication, docs can use GitHub source installs; after publication, docs can use the package name.

Alternatives considered:
- `uv run htb`: good for contributors but keeps the product tied to a checked-out repo.
- `pip install --user`: works sometimes, but PATH handling and externally-managed Python environments are more fragile on macOS/Homebrew systems.
- npm wrapper: adds a second ecosystem without solving any current Python packaging need.

### Decision: Add a conservative shell installer rather than a custom binary installer

The `curl` installer should be a thin bootstrapper. It should detect whether `uv` or `pipx` is available, prefer an isolated CLI tool install, install AGILE-AI-HTB from the configured source, check `command -v htb`, and report PATH guidance if the command is not visible.

Alternatives considered:
- Vendored standalone binary: more polished eventually, but higher build/release complexity now.
- Shell script that modifies profile files automatically: convenient but risky; better to print exact PATH guidance and avoid surprising shell changes.

### Decision: Homebrew starts as release/tap documentation plus formula scaffolding

Homebrew is valuable for macOS onboarding, but a clean Homebrew formula is easiest after release artifacts and checksums exist. The first implementation should document the intended `brew tap` / `brew install` path and add maintainable scaffolding or formula notes without pretending the tap is already published.

Alternatives considered:
- Block this change until Homebrew is fully published: unnecessary; `pipx` and `curl` can ship earlier.
- Use Homebrew to call arbitrary `curl | sh`: easier but less acceptable as a polished Homebrew formula.

### Decision: Separate operator install docs from contributor workflow docs

README/getting-started should present bare installed `htb` commands for operators. Contributor sections should retain `uv run pytest` and may mention `uv run htb` for repo-local development.

Alternatives considered:
- Replace all `uv run htb` references: would hurt contributor clarity and archived runbooks.
- Keep all docs on `uv run`: fails the requested install UX.

## Risks / Trade-offs

- [Risk] PATH issues after `pipx`/`uv tool` install can still prevent bare `htb` from resolving. → Mitigation: installer and docs must check `command -v htb` and print `pipx ensurepath` / `uv tool update-shell` guidance.
- [Risk] GitHub-source installs may use moving `main` until PyPI releases exist. → Mitigation: document GitHub install as pre-release/dev, and switch public docs to package-name install once published.
- [Risk] Homebrew docs may imply availability before a tap exists. → Mitigation: label tap/formula status explicitly and include a task to validate or defer public Homebrew wording until the tap is real.
- [Risk] Installer scripts can become a security concern. → Mitigation: keep the script small, avoid secret handling, avoid automatic shell profile edits, and test it with disposable install targets.
