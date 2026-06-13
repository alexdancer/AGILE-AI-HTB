# AGILE-AI-HTB

AGILE-AI-HTB is portal-first token-budget governance harness for AI coding agents. It wraps OpenAI-compatible chat requests, applies guardrails, records token usage, surfaces alarms, and keeps human operators in control.

## Local setup

```bash
uv run --python 3.11 --extra test pytest -q
uv run --python 3.11 htb --help
```

Set operator portal token before starting server:

```bash
export TOKEN_TRACKER_PORTAL_TOKEN=DEMO_PORTAL_TOKEN_2099
uv run --python 3.11 htb serve --host 127.0.0.1 --port 8000
```

Open portal:

```text
http://localhost:8000/login
```

Use same token from `TOKEN_TRACKER_PORTAL_TOKEN`. Browser login sets signed HttpOnly 12-hour cookie. Bearer auth still works for operators:

```bash
curl -H "Authorization: Bearer $TOKEN_TRACKER_PORTAL_TOKEN" http://localhost:8000/dashboard
```

## Seed synthetic demo tasks

```bash
uv run --python 3.11 htb seed-demo
```

This inserts `DEMO_TASK_2099_*` SNIP tasks into SQLite. Data is synthetic only.

## Docker demo

```bash
export TOKEN_TRACKER_PORTAL_TOKEN=DEMO_PORTAL_TOKEN_2099

docker compose build
docker compose up -d
curl -fsS http://localhost:8000/health
docker compose down
```

Container listens on port 8000, persists SQLite at `/data/harness.db`, and reads `guardrails.yaml` from `/app/guardrails.yaml`. Compose mounts local `guardrails.yaml` read-only and uses image tag `agile-ai-htb:local`.

## Config

Useful env vars:

- `TOKEN_TRACKER_DATABASE_PATH` — SQLite path, default `harness.db` locally, `/data/harness.db` in Docker.
- `TOKEN_TRACKER_GUARDRAILS_PATH` — guardrails YAML path.
- `TOKEN_TRACKER_PORTAL_TOKEN` — operator login/bearer token.
- `TOKEN_TRACKER_PORTAL_COOKIE_SECURE` — set `true` when serving over HTTPS.
- `TOKEN_TRACKER_PROVIDER_API_KEY_ENV` — name of env var holding provider key, default `PROVIDER_API_KEY`.

Provider keys belong in environment variables. They are not stored in repo or SQLite.

## Tests

```bash
uv run --python 3.11 --extra test pytest -q
uv run --python 3.11 python -m compileall -q src tests demo/snip/src demo/snip/tests
```

## optional live LiteLLM smoke

Default tests use fakes and spend no provider tokens. Optional live LiteLLM smoke requires provider keys in environment variables and may spend real tokens. Use only when operator approves spend.
