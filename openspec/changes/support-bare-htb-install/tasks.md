## 1. Packaging and install smoke

- [x] 1.1 Verify `pyproject.toml` package metadata is sufficient for source and wheel installs, including the existing `htb` console script entrypoint.
- [x] 1.2 Add or update packaging tests that assert installed metadata exposes the `htb` console script and `htb --help` reaches the operator CLI.
- [x] 1.3 Add a local disposable install smoke path for `pipx install` from the repository or built artifact, with cleanup instructions or automation.

## 2. Curl installer

- [x] 2.1 Add a small `install.sh` or equivalent public installer that detects `uv` first and `pipx` second.
- [x] 2.2 Make the installer install AGILE-AI-HTB through an isolated CLI install path, verify `command -v htb`, and print `htb init` as the next command on success.
- [x] 2.3 Make installer failures concise and actionable, including missing installer prerequisites and PATH remediation guidance, without reading or writing secrets.
- [x] 2.4 Add shell-level tests or script checks for installer branch behavior that can run without mutating the developer's real global tools.

## 3. Homebrew path

- [x] 3.1 Add Homebrew tap/formula documentation or scaffolding that states the intended `brew tap` / `brew install` command only when it is actually available.
- [x] 3.2 Add release notes or maintainer docs for how to validate the Homebrew formula after release artifacts and checksums exist.
- [x] 3.3 Ensure public docs fall back to validated `pipx` or curl install instructions until the Homebrew path is published and tested.

## 4. Public and contributor docs

- [x] 4.1 Update README quickstart to make public operators install first, then run bare `htb init`, `htb serve`, and `htb check`.
- [x] 4.2 Update `docs/GETTING_STARTED.md` and relevant setup docs to separate operator install commands from contributor repo-local `uv run` commands.
- [x] 4.3 Preserve model-layer/auth boundary wording: installing AGILE-AI-HTB does not install or authenticate OpenCode, Claude Code, Codex, Hermes, provider keys, or Worker credentials.
- [x] 4.4 Update support docs/templates to ask for install method and redacted `htb check` output using bare `htb check` where appropriate.

## 5. Verification

- [x] 5.1 Run the targeted packaging, installer, and docs tests added or updated for this change.
- [x] 5.2 Run `openspec validate support-bare-htb-install --strict`.
- [x] 5.3 Run fresh repo verification with `uv run pytest` after implementation changes are complete.
