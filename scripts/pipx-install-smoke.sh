#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/agile-ai-htb-pipx-smoke.XXXXXX")
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx is required for this smoke. Install it, then rerun: scripts/pipx-install-smoke.sh" >&2
  exit 1
fi

export PIPX_HOME="$TMP_DIR/pipx-home"
export PIPX_BIN_DIR="$TMP_DIR/bin"
mkdir -p "$PIPX_HOME" "$PIPX_BIN_DIR"

pipx install --force "$ROOT_DIR"
PATH="$PIPX_BIN_DIR:$PATH"
export PATH

htb --help >/dev/null
mkdir -p "$TMP_DIR/workspace"
cd "$TMP_DIR/workspace"
htb init >/dev/null
test -s .htb/config.toml
test -s .htb/secrets.env
test -s .htb/guardrails.yaml

echo "Disposable pipx install smoke passed: htb --help and htb init"
