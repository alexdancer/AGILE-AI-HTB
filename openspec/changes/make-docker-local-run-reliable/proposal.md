## Why

The repo already has a Dockerfile and Compose file, but the current Docker path is under-specified and mixes legacy model envs with container runtime config. Operators need a boring local Docker run that proves the Control Plane/Portal starts, persists SQLite data, exposes health, and states its Worker-launch boundary clearly.

## What Changes

- Keep Docker local run as one existing app container: no Postgres, Redis, nginx, Docker-in-Docker, or extra platform services.
- Tighten Compose env to use canonical control-plane model settings and portal token config instead of legacy/provider-mixed defaults.
- Preserve `/data/harness.db` as the persisted SQLite database and `/app/guardrails.yaml` as the guardrails path.
- Add one Docker smoke verification path that builds/starts Compose, checks `/health` and `/login`, runs `htb seed-demo` inside the container, verifies `/data/harness.db`, and cleans up.
- Document that Docker readiness means containerized Control Plane/Portal readiness, not host-native OpenCode/Claude/Codex/Hermes Worker Adapter readiness.

## Capabilities

### New Capabilities
- `docker-local-run`: Defines the supported local Docker/Compose runtime contract, persistence, health, smoke verification, and container boundary.

### Modified Capabilities
- `operator-setup`: Extends operator setup requirements so Docker uses the same control-plane model language, secret handling, and readiness semantics as local `htb init` / `htb serve` flows.

## Impact

- Affected files likely include `Dockerfile`, `docker-compose.yml`, `.dockerignore`, README/deployment docs, and one small Docker smoke script or test command.
- No public API changes.
- No new runtime dependencies.
- Docker Compose remains local orchestrator; implementation should detect `docker-compose` first and fall back to `docker compose` for portability.
