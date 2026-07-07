#!/usr/bin/env sh
set -eu

PACKAGE_SOURCE="${AGILE_AI_HTB_INSTALL_SOURCE:-git+https://github.com/alexdancer/AGILE-AI-HTB.git}"

say() {
  printf '%s\n' "$1"
}

fail() {
  say "ERROR: $1" >&2
  exit 1
}

path_help() {
  say "Installed AGILE-AI-HTB, but 'htb' is not visible on PATH." >&2
  if command -v uv >/dev/null 2>&1; then
    say "Try: uv tool update-shell" >&2
  fi
  if command -v pipx >/dev/null 2>&1; then
    say "Try: pipx ensurepath" >&2
  fi
  say "Then restart your shell and run: htb init" >&2
}

say "Installing AGILE-AI-HTB operator CLI..."

if command -v uv >/dev/null 2>&1; then
  say "Using uv tool install from: $PACKAGE_SOURCE"
  uv tool install --force "$PACKAGE_SOURCE"
elif command -v pipx >/dev/null 2>&1; then
  say "Using pipx install from: $PACKAGE_SOURCE"
  pipx install --force "$PACKAGE_SOURCE"
else
  fail "Install uv or pipx first, then rerun this installer. macOS: 'brew install uv' or 'brew install pipx'."
fi

if command -v htb >/dev/null 2>&1; then
  say "Installed AGILE-AI-HTB."
  say "Next: htb init"
  say "Then: htb serve"
else
  path_help
  exit 1
fi
