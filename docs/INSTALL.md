# Installing AGILE-AI-HTB

AGILE-AI-HTB is distributed as a Python CLI package. The package exposes the `htb` operator command, so normal operators should install once and then run bare commands such as `htb init`, `htb serve`, and `htb check`.

## Recommended today: pipx from GitHub

Until the package is published to PyPI, install from the GitHub source URL:

```bash
pipx install "git+https://github.com/alexdancer/AI-Harness-Token-Tracker.git"
htb init
htb serve
```

If `htb` is not found after install, run:

```bash
pipx ensurepath
```

Then restart your shell and try `htb init` again.

## After PyPI release

Once the package is published, the public install command becomes:

```bash
pipx install agile-ai-htb
htb init
```

## Curl installer

The installer is a small bootstrapper. It prefers `uv tool install`, falls back to `pipx install`, verifies that `htb` is visible on `PATH`, and prints the next operator command.

```bash
curl -fsSL https://raw.githubusercontent.com/alexdancer/AI-Harness-Token-Tracker/main/install.sh | sh
htb init
```

For development or pre-release testing, override the source:

```bash
AGILE_AI_HTB_INSTALL_SOURCE="git+https://github.com/alexdancer/AI-Harness-Token-Tracker.git" \
  sh install.sh
```

The installer does not ask for or store API keys, portal tokens, Worker credentials, or native CLI auth. Configure the Control Plane after login at `/settings/control-plane`; configure native Worker CLIs such as OpenCode, Claude Code, Codex, and Hermes separately.

## Homebrew status

Homebrew is planned for macOS-friendly install, but the tap/formula is not published yet. Until it is validated, use `pipx` or the curl installer above.

Intended future command shape:

```bash
brew tap alexdancer/htb
brew install agile-ai-htb
htb init
```

Maintainer formula scaffolding lives in `packaging/homebrew/agile-ai-htb.rb.example` and must be updated with real release URLs and checksums before public Homebrew docs claim availability.

## Contributor checkout

For contributors working inside a repository checkout, keep using the repo-managed environment for tests and local development:

```bash
uv run pytest -q
uv run htb --help
```

`uv run htb ...` is a contributor convenience. It is not the normal public operator install path.

## Disposable pipx smoke

Maintainers can test the pipx install path without mutating their global pipx environment:

```bash
scripts/pipx-install-smoke.sh
```

The smoke uses temporary `PIPX_HOME` and `PIPX_BIN_DIR`, installs this checkout, runs `htb --help`, and removes the temporary environment on exit.
