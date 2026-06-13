# Render Deployment — AGILE-AI-HTB

> **Goal:** Deploy the AGILE-AI-HTB harness to Render as a Docker-based web service with persistent SQLite storage and HTTPS.

**Architecture:** FastAPI + uvicorn in Docker on Render Web Service, with a Render Disk mounted at `/data` for the SQLite database. LiteLLM uses `PROVIDER_API_KEY` for upstream LLM calls.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, SQLite, LiteLLM, Docker, Render

---

## Pre-flight: What works already

- ✅ Dockerfile exists — `python:3.11-slim`, installs package, exposes 8000
- ✅ Health check endpoint at `/health` returns `{"status": "ok"}`
- ✅ Guardrails YAML baked into the image at `/app/guardrails.yaml`
- ✅ SQLite paths via env vars (`TOKEN_TRACKER_DATABASE_PATH`, `TOKEN_TRACKER_GUARDRAILS_PATH`)
- ✅ Portal auth via `TOKEN_TRACKER_PORTAL_TOKEN` env var (bearer token + signed cookie)
- ✅ `PORTAL_COOKIE_SECURE` flag for HTTPS-only cookies
- ✅ `htb serve` CLI entry point

## What needs to change

### Task 1: Make port dynamic for Render

**Problem:** Render injects `PORT` env var at runtime. The Dockerfile CMD hardcodes `--port 8000`.

**File:** `Dockerfile:18`

**Fix:** Change the CMD to read `$PORT`:

```dockerfile
CMD ["sh", "-c", "htb serve --host 0.0.0.0 --port ${PORT:-8000}"]
```

The `--database-path` and `--guardrails-path` are already set via env vars in the Dockerfile, so no CLI override needed.

### Task 2: Add Render Disk for SQLite persistence

**Problem:** Render containers have ephemeral filesystems. SQLite data is lost on every deploy/restart without a persistent disk.

**Solution:** Create a Render Disk and mount it at `/data` (the Dockerfile already writes the DB there via `TOKEN_TRACKER_DATABASE_PATH=/data/harness.db`).

This is done in the Render Dashboard (not in code):
- Disk name: `harness-data`
- Mount path: `/data`
- Size: 1 GB (Render free tier gives 1 GB; SQLite for this use case is tiny)

### Task 3: Set required environment variables in Render

Render Dashboard → Web Service → Environment:

| Variable | Value | Notes |
|---|---|---|
| `TOKEN_TRACKER_DATABASE_PATH` | `/data/harness.db` | Already in Dockerfile, but explicit is safer |
| `TOKEN_TRACKER_GUARDRAILS_PATH` | `/app/guardrails.yaml` | Already baked in |
| `TOKEN_TRACKER_PORTAL_TOKEN` | `<generate a strong random token>` | Use `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `PROVIDER_API_KEY` | `<your LiteLLM provider key>` | Required for LLM proxy / estimation |
| `TOKEN_TRACKER_PORTAL_COOKIE_SECURE` | `true` | Render gives HTTPS by default |
| `TOKEN_TRACKER_TIMEZONE` | `UTC` (or your zone) | Timezone for daily budget reset |
| `PYTHONUNBUFFERED` | `1` | Already in Dockerfile |
| `PYTHONDONTWRITEBYTECODE` | `1` | Already in Dockerfile |

## Render Dashboard Setup Steps

1. **Push to GitHub** — Render pulls from a Git repo. Ensure the repo is pushed.

2. **New Web Service** → "Build and deploy from a Git repository" → connect repo.

3. **Configure:**
   - **Name:** `agile-ai-htb` (or your preference)
   - **Runtime:** Docker
   - **Region:** Oregon (closest to you on the free tier)
   - **Instance Type:** Free (512 MB RAM, shared CPU) — sufficient for this app
   - **Health Check Path:** `/health`

4. **Add Disk:**
   - Name: `harness-data`
   - Mount path: `/data`
   - Size: 1 GB

5. **Add Environment Variables** (see table above).

6. **Deploy.** First deploy takes ~3-5 minutes (Docker build + container start).

7. **Verify:**
   ```bash
   curl https://<your-service>.onrender.com/health
   # {"status":"ok"}
   ```

8. **Seed demo data (optional):**
   Render's shell tab (or one-off job):
   ```bash
   htb seed-demo
   ```

## Optional: Add `render.yaml` for Blueprint deploys

If you want IaC (Infrastructure as Code), add this at repo root. Otherwise skip — the Dashboard UI is fine for a single service.

```yaml
services:
  - type: web
    name: agile-ai-htb
    runtime: docker
    region: oregon
    plan: free
    healthCheckPath: /health
    envVars:
      - key: TOKEN_TRACKER_DATABASE_PATH
        value: /data/harness.db
      - key: TOKEN_TRACKER_GUARDRAILS_PATH
        value: /app/guardrails.yaml
      - key: TOKEN_TRACKER_PORTAL_COOKIE_SECURE
        value: "true"
      - key: TOKEN_TRACKER_TIMEZONE
        value: UTC
      - key: TOKEN_TRACKER_PORTAL_TOKEN
        sync: false        # set manually in dashboard — not committed
      - key: PROVIDER_API_KEY
        sync: false        # set manually in dashboard — not committed
    disk:
      name: harness-data
      mountPath: /data
      sizeGB: 1
```

## Risks & Notes

- **Free tier cold start:** Render free web services spin down after 15 min of inactivity. First request after idle takes ~30-60s. If this is a demo, ping it with a cron or uptime monitor.
- **SQLite on network FS:** Render Disks are network-attached. SQLite warns about this but works fine at this scale (single writer, low concurrency).
- **LiteLLM costs:** Every estimation/task-routing call goes through LiteLLM → your provider. Set `PROVIDER_API_KEY` carefully.
- **Secrets not committed:** Both `TOKEN_TRACKER_PORTAL_TOKEN` and `PROVIDER_API_KEY` are secrets. Never commit them to the repo. Set them in Render's dashboard or via `render.yaml` with `sync: false`.
- **Guardrails customization:** The `guardrails.yaml` is baked into the Docker image. If you need to change guardrails often, mount it from a Render Disk or use a different approach (env-override, mounted config file). For now, baking is fine — redeploy to update.

## Verification Commands

After deploy:

```bash
# Health check
curl -s https://<service>.onrender.com/health | jq

# Portal login (get cookie)
curl -s -c cookies.txt -X POST https://<service>.onrender.com/portal/login \
  -d "token=$TOKEN_TRACKER_PORTAL_TOKEN"
# Should redirect to /portal

# Tasks API (with cookie)
curl -s -b cookies.txt https://<service>.onrender.com/tasks | jq '.[0]'
```

## Task Execution Order

1. Fix Dockerfile CMD to use `$PORT` (Task 1)
2. Commit + push to GitHub
3. Create Render Web Service + Disk + Env Vars (Tasks 2, 3)
4. Verify with health check
5. (Optional) Seed demo data
6. (Optional) Add `render.yaml`
