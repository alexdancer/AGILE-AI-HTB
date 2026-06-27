# Deploy AGILE-AI-HTB to Render

Render is the target cloud platform. This runbook covers first deploy, secret setup, and ongoing operation.

## Prerequisites

- Render account (free tier works)
- GitHub repo connected to Render
- Dockerfile and render.yaml committed to the repo
- An LLM provider API key (OpenAI, Anthropic, etc.)

## Architecture

```
Render Load Balancer (TLS)
  └─ Web Service: agile-ai-htb (Docker)
       ├─ FastAPI on port $PORT (Render-injected)
       ├─ SQLite at /data/harness.db (Render Disk, persistent)
       └─ guardrails.yaml at /app/guardrails.yaml (from image)
```

## Step-by-step first deploy

### 1. Push render.yaml to your repo

The repo already has `render.yaml` at the root. Render auto-detects it as a Blueprint.

```bash
git add render.yaml Dockerfile .dockerignore docker-compose.yml
git commit -m "feat: add Render deployment Blueprint and Dockerfile"
git push origin main
```

### 2. Create the Render Blueprint

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New → Blueprint**
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates:
   - Web Service: `agile-ai-htb`
   - Persistent Disk: `harness-data` (1 GB, mounted at `/data`)

### 3. Create the Render Disk (before first deploy)

If the Blueprint didn't auto-create the disk:

1. In the Render dashboard, go to **Disks**
2. Click **New Disk**
3. Name: `harness-data`, Size: 1 GB, Mount Path: `/data`
4. Attach to service `agile-ai-htb`

### 4. Set secrets in Render dashboard

Go to **agile-ai-htb → Environment** and add these secrets:

| Key | What it is | Example |
|---|---|---|
| `TOKEN_TRACKER_PORTAL_TOKEN` | Password for the portal web UI | `my-secure-portal-password` |
| `AGILE_AI_HTB_CONTROL_PROVIDER` | Direct provider identifier | `openai`, `anthropic`, or `openai-compatible` |
| `AGILE_AI_HTB_CONTROL_MODEL` | Control-plane/proxy upstream model | `gpt-4o-mini` or `claude-sonnet-4-20250514` |
| `AGILE_AI_HTB_CONTROL_API_KEY` | Your configured provider's API key | `sk-...` or `sk-ant-...` |
| `AGILE_AI_HTB_CONTROL_BASE_URL` | Optional OpenAI-compatible upstream base URL | `https://provider.example/v1` |

The `render.yaml` already declares these with `sync: false` so they won't be overwritten on re-deploy.

### 5. Deploy

The first deploy starts automatically after connecting the repo. If you need to trigger manually, click **Manual Deploy → Deploy latest commit**.

First deploy takes ~5 minutes (image build + disk provisioning).

### 6. Verify

```bash
# Health check
curl -s https://agile-ai-htb.onrender.com/health
# {"status":"ok"}

# Portal
open https://agile-ai-htb.onrender.com/login
# Log in with the TOKEN_TRACKER_PORTAL_TOKEN value
```

## Env var reference

All env vars read by `Settings()`:

| Variable | Default | Purpose |
|---|---|---|
| `TOKEN_TRACKER_DATABASE_PATH` | `harness.db` | SQLite path (Render: `/data/harness.db`) |
| `TOKEN_TRACKER_GUARDRAILS_PATH` | `guardrails.yaml` | Guardrail config (Render: `/app/guardrails.yaml`) |
| `TOKEN_TRACKER_TIMEZONE` | `local` | Timezone for midnight reset (`UTC`, `US/Pacific`, etc.) |
| `TOKEN_TRACKER_ESTIMATOR_MODEL` | `gpt-4o-mini` | Legacy alias for the control-plane model |
| `TOKEN_TRACKER_CONTROL_PLANE_PROVIDER` / `AGILE_AI_HTB_CONTROL_PROVIDER` | `openai` | Direct upstream provider (`openai`, `openai-compatible`, or `anthropic`) |
| `TOKEN_TRACKER_CONTROL_PLANE_MODEL` / `AGILE_AI_HTB_CONTROL_MODEL` | `gpt-4o-mini` | Model used by control-plane and proxy upstream calls |
| `TOKEN_TRACKER_TASK_BREAKDOWN_MODEL` / `AGILE_AI_HTB_TASK_BREAKDOWN_MODEL` | control-plane model | Optional Task Breakdown Agent model. Falls back to the control-plane model and records spend as control-plane orchestration tokens labeled `task_breakdown`, not Worker Adapter spend. |
| `AGILE_AI_HTB_CONTROL_API_KEY_ENV` | `AGILE_AI_HTB_CONTROL_API_KEY` | Name of the env var holding the control-plane API key |
| `AGILE_AI_HTB_CONTROL_API_KEY` | — | Control-plane/proxy upstream provider API key |
| `AGILE_AI_HTB_CONTROL_BASE_URL` | — | Optional OpenAI-compatible upstream base URL |
| `TOKEN_TRACKER_PORTAL_TOKEN_ENV` | `TOKEN_TRACKER_PORTAL_TOKEN` | Name of the env var holding the portal password |
| `TOKEN_TRACKER_PORTAL_COOKIE_SECURE` | `false` | Set `true` for HTTPS (Render behind TLS) |
| `TOKEN_TRACKER_PROVIDER_API_KEY_ENV` | `PROVIDER_API_KEY` | Legacy control-plane API key env fallback |

Local operator runs can change the control-plane provider/model at `/settings/control-plane` without restarting. Save writes non-secret fields to `.htb/config.toml`, keeps API key values in `.htb/secrets.env` or environment, and changes the setup state to `needs test` until the connection test passes.

## Hot tips

### SQLite persistence

The Render Disk (`/data`) survives deploys and restarts. If you ever recreate the disk, all task/session/token history is lost. Back it up:

```bash
# Download the database
curl -o backup.db https://agile-ai-htb.onrender.com/health  # won't work; use scp or Render shell
# Better: Render dashboard → Shell → cp /data/harness.db /tmp/ && download from there
```

### Cold starts

Free tier spins down after 15 minutes of inactivity. First request takes 30-60s to wake up. Keep it warm by pinging `/health` every 10 minutes (e.g., a cronjob or UptimeRobot).

```bash
# One-liner cron warmup
*/10 * * * * curl -sf https://agile-ai-htb.onrender.com/health > /dev/null
```

### Updating guardrails

The guardrails YAML is baked into the Docker image at build time. To change guardrails:
1. Edit `guardrails.yaml` locally
2. Commit and push — Render auto-redeploys

### Changing the portal password

1. Update `TOKEN_TRACKER_PORTAL_TOKEN` in Render dashboard → Environment
2. Redeploy or restart the service

### Viewing logs

Render dashboard → agile-ai-htb → Logs. Shows uvicorn output, direct provider proxy requests, and any errors.

### Shell access

Render dashboard → agile-ai-htb → Shell. Useful for:
- Inspecting the database: `sqlite3 /data/harness.db ".tables"`
- Running seed-demo: `htb seed-demo --database-path /data/harness.db`
- Checking guardrails: `cat /app/guardrails.yaml`

## Local Docker verification

Before pushing, verify the image builds and runs:

```bash
export TOKEN_TRACKER_PORTAL_TOKEN="replace-with-local-token"
export AGILE_AI_HTB_CONTROL_PROVIDER="openai"
export AGILE_AI_HTB_CONTROL_MODEL="gpt-5.4-mini"
# Optional for model-powered checks:
# export AGILE_AI_HTB_CONTROL_API_KEY="replace-with-provider-key"

docker-compose up -d --build
curl -s http://localhost:8000/health
curl -s http://localhost:8000/login >/dev/null
docker-compose exec agile-ai-htb htb seed-demo
# Optional readiness report; exits nonzero until required secrets are set.
docker-compose exec agile-ai-htb htb check || true
docker-compose down

# Or run the full local smoke path. It picks docker-compose first, falls back to
# docker compose, verifies /data/harness.db across container recreation, and cleans up.
# It stops and recreates this repo's Compose service; named volumes are kept.
scripts/docker-smoke.sh
```

Local Docker proves the containerized Control Plane/Portal. It does not automatically provide host OpenCode, Claude Code, Codex, Hermes, local repo paths, or host credentials; Worker launch readiness still comes from configured Worker Adapter and tracking-mode checks.
