## Why

First-time operators should be able to install AGILE-AI-HTB once and then run `htb init`, `htb serve`, and `htb check` directly. Requiring `uv run htb ...` makes the product feel like a repo-only developer workflow instead of an installable operator CLI.

## What Changes

- Add a supported CLI distribution path where the installed package exposes the existing `htb` console script on `PATH`.
- Document and verify `pipx` installation as the primary Python-native install path, including GitHub install before PyPI release and package-name install after publication.
- Add a `curl | sh` installer that selects a safe available installer (`uv tool` or `pipx`), installs AGILE-AI-HTB, checks that `htb` is on `PATH`, and prints the next operator commands.
- Add Homebrew distribution scaffolding/docs so macOS users can install through a tap once release artifacts are available.
- Update public onboarding docs to present installed bare `htb` commands as the normal operator flow while preserving `uv run` for contributor/developer workflows.

## Capabilities

### New Capabilities
- `cli-distribution-install`: Defines supported install channels that make the `htb` command available without `uv run`, including `pipx`, `curl` installer, and Homebrew onboarding.

### Modified Capabilities
- `public-release-onboarding`: Update first-run onboarding so public users install the CLI first, then use bare `htb init`, `htb serve`, and `htb check`.
- `operator-setup`: Clarify that operator setup commands are bare installed CLI commands, while repo-local contributor commands may still use `uv run`.

## Impact

- Packaging metadata and release documentation for the existing Python console script.
- New installer script and tests/smoke checks for install instructions where practical.
- README and getting-started docs updated to separate operator install UX from contributor/dev workflow.
- Optional Homebrew tap/formula documentation or scaffolding; no npm distribution required.
