# Local Demo Runbook: Direct Provider Harness with `gpt-5.4-mini`

This runbook verifies the local AGILE-AI-HTB / AI Harness Token Tracker demo with the direct OpenAI provider client and the official OpenAI model:

```text
gpt-5.4-mini
```

## What this demo proves

- The FastAPI portal starts locally.
- The direct OpenAI control-plane provider path uses `AGILE_AI_HTB_CONTROL_*` settings.
- GPT-5.x OpenAI calls use `max_completion_tokens` instead of unsupported `max_tokens`.
- Estimation can call `gpt-5.4-mini` and record control-plane token usage.
- The OpenAI-compatible `/v1/chat/completions` proxy path is exercised.
- The synthetic `demo_worker` is launchable with budget-authoritative proxy-governed tracking evidence.
- Token usage is written to the SQLite ledger.
- Provider keys are not copied/fanned out into generic provider env vars.

## Fixed compatibility assumptions

This runbook assumes the local branch includes the fixes verified by the test suite:

- OpenAI GPT-5.x requests send `max_completion_tokens` instead of `max_tokens`.
- The seeded `demo_worker` includes `gpt-5.4-mini` and budget-authoritative proxy-governed tracking evidence.
- Demo worker templates can use the generated `{session_api_key}`.
- Worker verification template errors are reported as configuration errors instead of `worker adapter not found`.

If you still see `Unsupported parameter: 'max_tokens'`, stop all stale local servers and restart from this checkout.

---

## 0. Start clean

```bash
cd /Users/alex/Documents/Fired-Fest-Token-Traker-Harness/AI-Harness-Token-Tracker

rm -rf .demo
mkdir -p .demo
```

---

## 1. Verify the codebase first

```bash
uv run pytest tests/test_budgeted_launch.py tests/test_local_execution_backend.py tests/test_tasks_api.py
uv run pytest
openspec validate fix-local-demo-launch-and-task-intake-evals --strict
```

Expected result:

```text
69 passed
274 passed
Change 'fix-local-demo-launch-and-task-intake-evals' is valid
```

The exact warning count/timing may vary.

---

## 2. Set local demo environment variables

```bash
export TOKEN_TRACKER_DATABASE_PATH="$PWD/.demo/harness.db"
export TOKEN_TRACKER_PORTAL_TOKEN="demo-token"

export AGILE_AI_HTB_CONTROL_PROVIDER="openai"
export AGILE_AI_HTB_CONTROL_MODEL="gpt-5.4-mini"
```

### zsh-safe secret prompt

Do **not** paste real keys into terminal history.

```bash
printf "OpenAI API key: "
stty -echo
IFS= read -r AGILE_AI_HTB_CONTROL_API_KEY
stty echo
echo
export AGILE_AI_HTB_CONTROL_API_KEY
```

### Ensure the demo is not relying on generic provider env vars

```bash
unset OPENAI_API_KEY
unset ANTHROPIC_API_KEY
unset COHERE_API_KEY
unset GROQ_API_KEY
```

The direct provider client should use:

```text
AGILE_AI_HTB_CONTROL_API_KEY
```

not `OPENAI_API_KEY`.

---

## 3. Start the portal with Local Runner enabled

In Terminal A:

```bash
uv run htb serve --local-runner --host 127.0.0.1 --port 8000
```

Leave this process running.

---

## 4. Smoke-check the server

In Terminal B:

```bash
cd /Users/alex/Documents/Fired-Fest-Token-Traker-Harness/AI-Harness-Token-Tracker

export TOKEN_TRACKER_DATABASE_PATH="$PWD/.demo/harness.db"
export TOKEN_TRACKER_PORTAL_TOKEN="demo-token"
export BASE_URL="http://127.0.0.1:8000"

curl -fsS "$BASE_URL/health"
```

Expected:

```json
{"status":"ok"}
```

Check root redirect:

```bash
curl -i -s "$BASE_URL/" | head
```

Expected: an HTTP redirect to `/login`.

---

## 5. Seed synthetic demo tasks and demo adapter

```bash
uv run htb seed-demo
```

Expected:

```text
seed-demo inserted 6 synthetic DEMO tasks into .../.demo/harness.db
```

The seeded demo adapter is repaired automatically if an older/stale `demo_worker` row exists. It should include `gpt-5.4-mini` and budget-authoritative proxy-governed verification evidence.

Verify:

```bash
sqlite3 "$TOKEN_TRACKER_DATABASE_PATH" \
  "select id, verification_status, supported_models_json, json_extract(verification_evidence_json,'$.tracking_mode'), json_extract(verification_evidence_json,'$.tracking_authoritative') from worker_adapters where id = 'demo_worker';"
```

Expected shape:

```text
demo_worker|verified|["gpt-5.4-mini",...]|proxy_governed|1
```

---

## 6. Open the UI

Open:

```text
http://127.0.0.1:8000/login
```

Log in with:

```text
demo-token
```

Then check:

```text
/dashboard
/board
/settings/workers
/settings/control-plane
```

Expected:

- Board has `DEMO_TASK_2099_T1` through `DEMO_TASK_2099_T6`.
- Worker settings show `Demo Worker`.
- Control plane page shows direct provider config.
- No LiteLLM wording should be part of the flow.

---

## 7. Control-plane test route

Run:

```bash
curl -sS -X POST "$BASE_URL/settings/control-plane/test" \
  -H "Authorization: Bearer ${TOKEN_TRACKER_PORTAL_TOKEN}" \
  | python3 -m json.tool
```

Expected result:

```json
{
  "passed": true,
  "status": {
    "id": "control_plane_model",
    "online": true
  }
}
```

You can confirm from SQLite:

```bash
sqlite3 "$TOKEN_TRACKER_DATABASE_PATH" \
  "select id, online, json_extract(details_json,'$.model'), json_extract(details_json,'$.provider') from execution_backend_status where id = 'control_plane_model';"
```

Expected diagnostic shape:

```text
control_plane_model|1|gpt-5.4-mini|openai
```

---

## 8. Prove estimation uses the control-plane model

Run:

```bash
curl -fsS -X POST "$BASE_URL/estimate" \
  -H "Authorization: Bearer ${TOKEN_TRACKER_PORTAL_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "DEMO 2099: Add a dry-run flag to the synthetic snip CLI",
    "adapter_id": "demo_worker"
  }' \
  > /tmp/agile_ai_htb_estimate.json

python3 -m json.tool /tmp/agile_ai_htb_estimate.json
```

Expected:

- Response includes a task `id`.
- Status is `Estimated`.
- Has `estimate_tokens`.
- Recommended worker model should be one of the seeded `demo_worker` supported models, including `gpt-5.4-mini`.

Check the token ledger:

```bash
sqlite3 "$TOKEN_TRACKER_DATABASE_PATH" \
  "select usage_kind, model, prompt_tokens, completion_tokens, total_tokens, json_extract(raw_usage_json,'$.spend_category') from token_turns order by id;"
```

Expected row:

```text
estimation|gpt-5.4-mini|...|...|...|control_plane
```

This proves:

- direct OpenAI provider call works
- `AGILE_AI_HTB_CONTROL_*` config works
- control-plane spend is tracked separately

---

## 9. Start a proxy session

Run:

```bash
curl -fsS -X POST "$BASE_URL/session/start" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "DEMO 2099 direct proxy test",
    "model": "gpt-5.4-mini"
  }' \
  > /tmp/agile_ai_htb_session.json

python3 -m json.tool /tmp/agile_ai_htb_session.json
```

Extract the session key into the current shell:

```bash
export SESSION_BEARER="$(
python3 - <<'PY'
import json
print(json.load(open('/tmp/agile_ai_htb_session.json'))['session_api_key'])
PY
)"
```

Do not print or paste this session key into logs.

---

## 10. Test `/v1/chat/completions` proxy compatibility

Run:

```bash
curl -sS -X POST "$BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer ${SESSION_BEARER}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {
        "role": "user",
        "content": "Reply with exactly: AGILE-AI-HTB direct proxy OK"
      }
    ]
  }' \
  > /tmp/agile_ai_htb_proxy.json

python3 -m json.tool /tmp/agile_ai_htb_proxy.json
```

Expected:

- HTTP `200`.
- Response has `choices[0].message.content`.
- No `Unsupported parameter: 'max_tokens'` error.

---

## 11. Test streaming proxy behavior

Run:

```bash
curl -N -sS -X POST "$BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer ${SESSION_BEARER}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "Stream three short words."
      }
    ]
  }'
```

Expected:

- SSE-style chunks are printed.
- No `Unsupported parameter: 'max_tokens'` provider error.

---

## 12. Try proxy-governed demo Worker launch

Run:

```bash
curl -sS -X POST "$BASE_URL/tasks/DEMO_TASK_2099_T1/launch" \
  -H "Authorization: Bearer ${TOKEN_TRACKER_PORTAL_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "adapter_id": "demo_worker",
    "model": "gpt-5.4-mini",
    "proxy_url": "http://127.0.0.1:8000/v1",
    "estimate_tokens": 8000,
    "budget_override": true
  }' \
  > /tmp/agile_ai_htb_launch.json

python3 -m json.tool /tmp/agile_ai_htb_launch.json
```

Expected success includes:

- `launch_guardrails.passed` is `true`.
- Task gets a `session_id`.
- Worker calls go through harness proxy.
- Token ledger records Worker execution.

If it fails, check the task metadata:

```bash
sqlite3 "$TOKEN_TRACKER_DATABASE_PATH" \
  "select id, status, recommended_model, estimate_tokens, metadata_json from tasks where id = 'DEMO_TASK_2099_T1';"
```

Known stale-server/stale-DB failure signals:

```text
Budget-authoritative Worker tracking has not been verified for this adapter.
worker adapter not found
Unsupported parameter: 'max_tokens'
```

If any of those appear, stop all servers, confirm ports 8000/8001/8002 are down, rerun `uv run htb seed-demo`, then restart only one server on port 8000.

---

## 13. Check token ledger and spend separation

Run:

```bash
sqlite3 "$TOKEN_TRACKER_DATABASE_PATH" \
  "select usage_kind, model, prompt_tokens, completion_tokens, total_tokens, json_extract(raw_usage_json,'$.spend_category'), json_extract(raw_usage_json,'$.usage_source') from token_turns order by id;"
```

Expected after step 8:

```text
estimation|gpt-5.4-mini|...|...|...|control_plane|control_plane
```

Expected after proxy/session/launch steps:

```text
task_execution|gpt-5.4-mini|...|...|...|worker_execution|harness_proxy
```

The exact `usage_kind` may vary between direct proxy calls and launched worker calls, but the important proof is:

```text
worker_execution|harness_proxy
```

---

## 14. Check the UI proof

Open:

```text
http://127.0.0.1:8000/dashboard
http://127.0.0.1:8000/board
http://127.0.0.1:8000/sessions
```

Expected:

- Dashboard loads.
- Board shows seeded demo tasks and any estimated task from step 8.
- Sessions page shows the estimation/proxy/launch sessions.
- Token totals include separated control-plane and Worker execution spend.
- Reports show proxy-governed token usage.

---

## 15. Prove provider keys were not fanned out

Run:

```bash
python3 - <<'PY'
import os
for name in [
    'AGILE_AI_HTB_CONTROL_API_KEY',
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'COHERE_API_KEY',
    'GROQ_API_KEY',
]:
    print(name, 'set' if os.getenv(name) else 'unset')
PY
```

Expected:

```text
AGILE_AI_HTB_CONTROL_API_KEY set
OPENAI_API_KEY unset
ANTHROPIC_API_KEY unset
COHERE_API_KEY unset
GROQ_API_KEY unset
```

This proves the demo shell is not relying on generic provider-key fan-out.

---

## 16. Optional: OpenAI-compatible provider path

Stop the server, then restart with an OpenAI-compatible endpoint:

```bash
export TOKEN_TRACKER_DATABASE_PATH="$PWD/.demo/compatible-harness.db"
export TOKEN_TRACKER_PORTAL_TOKEN="demo-token"

export AGILE_AI_HTB_CONTROL_PROVIDER="openai-compatible"
export AGILE_AI_HTB_CONTROL_MODEL="gpt-5.4-mini"
export AGILE_AI_HTB_CONTROL_BASE_URL="<your-compatible-provider-base-url>"

printf "Compatible provider API key: "
stty -echo
IFS= read -r AGILE_AI_HTB_CONTROL_API_KEY
stty echo
echo
export AGILE_AI_HTB_CONTROL_API_KEY

uv run htb serve --local-runner --host 127.0.0.1 --port 8000
```

Then seed the demo adapter:

```bash
uv run htb seed-demo
```

Repeat steps 7 through 15.

---

## 17. Optional: Anthropic direct-provider path

Anthropic does not serve `gpt-5.4-mini`. Use an Anthropic model to test the Anthropic direct client.

Stop the server, then:

```bash
export TOKEN_TRACKER_DATABASE_PATH="$PWD/.demo/anthropic-harness.db"
export TOKEN_TRACKER_PORTAL_TOKEN="demo-token"

export AGILE_AI_HTB_CONTROL_PROVIDER="anthropic"
export AGILE_AI_HTB_CONTROL_MODEL="claude-3-5-sonnet-20241022"

printf "Anthropic API key: "
stty -echo
IFS= read -r AGILE_AI_HTB_CONTROL_API_KEY
stty echo
echo
export AGILE_AI_HTB_CONTROL_API_KEY

uv run htb serve --local-runner --host 127.0.0.1 --port 8000
```

Test:

```bash
curl -sS -X POST "http://127.0.0.1:8000/settings/control-plane/test" \
  -H "Authorization: Bearer ${TOKEN_TRACKER_PORTAL_TOKEN}" \
  | python3 -m json.tool
```

Expected:

```json
{
  "passed": true
}
```

Anthropic streaming is intentionally unsupported by the current direct provider client.

---

## 18. Optional: real OpenCode native proof

Only do this if OpenCode is installed and logged in.

Terminal A must be running the portal.

Terminal B:

```bash
export TOKEN_TRACKER_PORTAL_TOKEN="demo-token"
export BASE_URL="http://127.0.0.1:8000"
export PROJECT_ROOT="$PWD"

scripts/local-opencode-readonly-demo.sh
```

Expected stages:

```text
1/4 Test AGILE-AI-HTB control-plane model connection
passed= True

2/4 Discover OpenCode Worker models
worker_model=...

3/4 Verify OpenCode native usage tracking
passed= True

4/4 Connect project + launch read-only proof
task=...
session=...
tracking_mode=native_usage
```

If this fails at discovery or verification, the portal may still be fine; local OpenCode may not be ready.

---

## Final pass criteria

```bash
uv run pytest tests/test_budgeted_launch.py tests/test_local_execution_backend.py tests/test_tasks_api.py
uv run pytest
openspec validate fix-local-demo-launch-and-task-intake-evals --strict
```

pass.

```bash
curl -fsS "$BASE_URL/health"
```

returns:

```json
{"status":"ok"}
```

`/settings/control-plane/test` returns:

```json
{"passed": true, ...}
```

Token ledger includes control-plane estimation spend:

```text
estimation|gpt-5.4-mini|...|control_plane
```

Token ledger includes Worker execution spend after launch:

```text
worker_execution|harness_proxy
```

Pages load:

```text
/dashboard
/board
/settings/control-plane
/settings/workers
/sessions
```
