## Context

Current Docker is already close: `Dockerfile` installs the package and runs `htb serve`; Compose exposes `8000:8000`, persists `/data/harness.db`, bind-mounts `guardrails.yaml`, and checks `/health`.

The rough edges are mostly contract drift:
- Compose uses legacy/mixed envs: `ANTHROPIC_API_KEY`, `PROVIDER_API_KEY`, and Claude Haiku as estimator default.
- Operator setup specs now center canonical control-plane env/config names.
- Docker has no single smoke verification path.
- Docker docs can imply more than the container can do. A containerized Portal does not automatically see host Worker CLIs, native auth, or local repo paths.

## Goals / Non-Goals

**Goals:**
- Make `docker-compose up --build` a supported local Control Plane/Portal startup path.
- Persist SQLite under `/data/harness.db` with the existing named volume.
- Keep guardrails mounted at `/app/guardrails.yaml`.
- Use canonical control-plane env naming for model setup.
- Add one small smoke verification path for Docker build/start/health/login/demo seed/database evidence.
- Document Docker's boundary with host-native Worker Adapters.

**Non-Goals:**
- No Postgres, Redis, nginx, Kubernetes, Docker socket, or Docker-in-Docker.
- No secret vault or committed `.env` file requirement.
- No host Worker CLI bridge in this slice.
- No new frontend/runtime service.

## Decisions

1. Keep one service.
   - Chosen: one `agile-ai-htb` service running `htb serve`.
   - Rejected: split web/worker/db stack. Current app uses FastAPI + in-process background executor + SQLite; extra services add moving parts without solving the reported Docker reliability gap.

2. Keep SQLite volume.
   - Chosen: named Compose volume mounted at `/data`, app DB path `/data/harness.db`.
   - Rejected: bind-mount repo-local DB by default. Named volume avoids dirtying the repo and matches container lifecycle better.

3. Canonical env first.
   - Chosen: Docker docs/Compose guide operators toward `AGILE_AI_HTB_CONTROL_PROVIDER`, `AGILE_AI_HTB_CONTROL_MODEL`, optional `AGILE_AI_HTB_CONTROL_BASE_URL`, `AGILE_AI_HTB_CONTROL_API_KEY`, and `TOKEN_TRACKER_PORTAL_TOKEN`.
   - Rejected: legacy provider aliases as primary path. They blur control-plane auth with Worker Adapter auth.

4. Smoke script over test framework machinery.
   - Chosen: one runnable smoke path that detects `docker-compose` before `docker compose`, starts the service, curls endpoints, checks DB file, recreates the service to prove named-volume persistence, then tears down.
   - Rejected: pytest plugin/fixture stack for Docker. Too much machinery for a local operator check.

5. Boundary in docs, not fake integration.
   - Chosen: state that Docker proves containerized Control Plane/Portal readiness only.
   - Rejected: mounting host CLIs/secrets/repos by default. That is risky, host-specific, and belongs in a later Local Runner bridge proposal if needed.

## Risks / Trade-offs

- Docker appears healthy while Worker launches remain disabled → Mitigation: docs and readiness text explicitly separate Control Plane readiness from Worker Adapter readiness.
- Local demo token is convenient but unsafe outside local dev → Mitigation: document `TOKEN_TRACKER_PORTAL_TOKEN` override.
- Smoke check needs Docker daemon → Mitigation: keep it as a local smoke command, not required for normal unit tests.
- Compose command varies by machine → Mitigation: smoke path chooses `docker-compose` first, then `docker compose`.

## Migration Plan

1. Update Compose env and docs.
2. Add smoke verification path.
3. Run `docker-compose config`, Docker smoke check, and `uv run pytest`.
4. Rollback by reverting Docker/docs/smoke files; app code and data schema remain unchanged.

## Open Questions

- Should Docker smoke live under `scripts/`, `tests/smoke/`, or README-only command block? Lazy default: `scripts/docker-smoke.sh`.
