#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
PORTAL_TOKEN="${TOKEN_TRACKER_PORTAL_TOKEN:-${PORTAL_TOKEN:-}}"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
VERIFY_MODEL="${WORKER_MODEL:-}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python || true)}"

if [[ -z "$PORTAL_TOKEN" ]]; then
  echo "Set TOKEN_TRACKER_PORTAL_TOKEN (portal password/token) before running." >&2
  exit 2
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3 is required for JSON parsing; install python3 or set PYTHON_BIN." >&2
  exit 2
fi
AUTH_HEADER="Authorization: Bearer $PORTAL_TOKEN"

api() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  local response_file status
  response_file="$(mktemp)"
  if [[ -n "$data" ]]; then
    status="$(curl -sS -o "$response_file" -w "%{http_code}" -X "$method" "$BASE_URL$path" \
      -H "$AUTH_HEADER" \
      -H "Content-Type: application/json" \
      --data "$data")"
  else
    status="$(curl -sS -o "$response_file" -w "%{http_code}" -X "$method" "$BASE_URL$path" \
      -H "$AUTH_HEADER")"
  fi
  if [[ "$status" -ge 400 ]]; then
    echo "Request $method $path returned HTTP $status:" >&2
    cat "$response_file" >&2
    echo >&2
    rm -f "$response_file"
    return 22
  fi
  cat "$response_file"
  rm -f "$response_file"
}

pick_first_model() {
  "$PYTHON_BIN" -c 'import json,sys
payload=json.load(sys.stdin)
models=payload.get("models") or []
if not models:
    raise SystemExit("No Worker models discovered")
print(models[0])'
}

pick_project_id() {
  "$PYTHON_BIN" -c 'import json,sys
payload=json.load(sys.stdin)
project=payload.get("project") or {}
if not project.get("id"):
    raise SystemExit("Project connect did not return project.id")
print(project["id"])'
}

echo "1/4 Test AGILE-AI-HTB control-plane model connection"
api POST /settings/control-plane/test >/tmp/agile_ai_htb_control_plane.json
"$PYTHON_BIN" -c 'import json; p=json.load(open("/tmp/agile_ai_htb_control_plane.json")); print("passed=", p.get("passed"))'

echo "2/4 Discover OpenCode Worker models"
api POST /settings/workers/opencode/discover-models >/tmp/agile_ai_htb_models.json
if [[ -z "$VERIFY_MODEL" ]]; then
  VERIFY_MODEL="$(pick_first_model </tmp/agile_ai_htb_models.json)"
fi
echo "worker_model=$VERIFY_MODEL"

echo "3/4 Verify OpenCode native usage tracking"
api POST /settings/workers/opencode/verify "{\"model\":\"$VERIFY_MODEL\",\"tracking_mode\":\"native_usage\"}" >/tmp/agile_ai_htb_verify.json
"$PYTHON_BIN" -c 'import json; p=json.load(open("/tmp/agile_ai_htb_verify.json")); print("passed=", p.get("passed")); print("reasons=", p.get("reasons"))'

echo "4/4 Connect project + launch read-only proof"
api POST /settings/project/connect "{\"root_path\":\"$PROJECT_ROOT\"}" >/tmp/agile_ai_htb_project.json
PROJECT_ID="$(pick_project_id </tmp/agile_ai_htb_project.json)"
api POST "/settings/project/$PROJECT_ID/read-only-proof" >/tmp/agile_ai_htb_readonly_proof.json
"$PYTHON_BIN" -c 'import json; p=json.load(open("/tmp/agile_ai_htb_readonly_proof.json")); print("task=", (p.get("task") or {}).get("id")); print("session=", (p.get("session") or {}).get("id")); print("tracking_mode=", ((p.get("task") or {}).get("metadata") or {}).get("tracking_mode"))'

echo "Done. Open $BASE_URL/dashboard and /sessions for separated control-plane vs Worker spend."
