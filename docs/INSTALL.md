# Installing Foreman AI HQ

Foreman AI HQ is distributed as a Python CLI package. The package exposes the `foremanctl` operator command, so normal operators should install once and then run bare commands such as `foremanctl init`, `foremanctl serve`, and `foremanctl check`.

## Recommended today: pipx from GitHub

Until the package is published to PyPI, install from the GitHub source URL:

```bash
pipx install "git+https://github.com/alexdancer/foreman-ai-hq.git"
cd /path/to/your/repo
foremanctl init
foremanctl serve
```

The installed `foremanctl` command is global. `foremanctl init` writes repo-local state under `.foreman/`; inside Git it targets the repository root, and outside Git it uses the current directory.

If `foremanctl` is not found after install, run:

```bash
pipx ensurepath
```

Then restart your shell and try `foremanctl init` again.

## After PyPI release

Once the package is published, the public install command becomes:

```bash
pipx install foreman-ai-hq
foremanctl init
```

## Curl installer

The installer is a small bootstrapper. It prefers `uv tool install`, falls back to `pipx install`, verifies that `foremanctl` is visible on `PATH`, and prints the next operator command.

```bash
curl -fsSL https://raw.githubusercontent.com/alexdancer/foreman-ai-hq/main/install.sh | sh
foremanctl init
```

For development or pre-release testing, override the source:

```bash
FOREMAN_AI_HQ_INSTALL_SOURCE="git+https://github.com/alexdancer/foreman-ai-hq.git" \
  sh install.sh
```

The installer does not ask for or store API keys, portal tokens, Worker credentials, or native CLI auth. Configure the Control Plane after login at `/settings/control-plane`; configure native Worker CLIs such as OpenCode, Claude Code, and Codex separately.

## Updating Foreman AI HQ

Updating replaces the global `foremanctl` CLI package. It does not delete or recreate repo-local `.foreman/` state such as `.foreman/config.toml`, `.foreman/secrets.env`, `.foreman/guardrails.yaml`, or `.foreman/harness.db`.

Before the PyPI release, rerun the curl installer:

```bash
curl -fsSL https://raw.githubusercontent.com/alexdancer/foreman-ai-hq/main/install.sh | sh
```

Or update the package directly with the installer you used:

```bash
pipx install --force "git+https://github.com/alexdancer/foreman-ai-hq.git"
```

```bash
uv tool install --force "git+https://github.com/alexdancer/foreman-ai-hq.git"
```

After the PyPI release, use the package upgrade command for your installer:

```bash
pipx upgrade foreman-ai-hq
```

```bash
uv tool upgrade foreman-ai-hq
```

## Homebrew status

Homebrew is planned for macOS-friendly install, but the tap/formula is not published yet. Until it is validated, use `pipx` or the curl installer above.

Intended future command shape:

```bash
brew tap alexdancer/foremanctl
brew install foreman-ai-hq
foremanctl init
```

Maintainer formula scaffolding lives in `packaging/homebrew/foreman-ai-hq.rb.example` and must be updated with real release URLs and checksums before public Homebrew docs claim availability.

## Contributor checkout

For contributors working inside a repository checkout, keep using the repo-managed environment for tests and local development:

```bash
uv run --extra test pytest -q
uv run foremanctl --help
```

`uv run foremanctl ...` is a contributor convenience. It is not the normal public operator install path.

## Disposable pipx smoke

Maintainers can test the pipx install path without mutating their global pipx environment:

```bash
scripts/pipx-install-smoke.sh
```

The smoke uses temporary `PIPX_HOME` and `PIPX_BIN_DIR`, installs this checkout, runs `foremanctl --help`, and removes the temporary environment on exit.
