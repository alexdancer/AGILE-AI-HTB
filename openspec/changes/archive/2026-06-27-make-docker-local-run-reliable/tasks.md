## 1. Runtime Contract

- [x] 1.1 Update `docker-compose.yml` to prefer canonical control-plane env vars and remove misleading legacy/provider-mixed defaults.
- [x] 1.2 Preserve single-service runtime, port `8000:8000`, `/data` volume, `/app/guardrails.yaml`, and `/health` healthcheck.
- [x] 1.3 Review `Dockerfile` and `.dockerignore` for only necessary build/runtime changes; avoid adding services or dependencies.

## 2. Smoke Verification

- [x] 2.1 Add one Docker smoke verification path that selects `docker-compose` before falling back to `docker compose`.
- [x] 2.2 Verify build/start, `/health`, `/login`, `/data/harness.db`, and cleanup in that smoke path.

## 3. Documentation

- [x] 3.1 Update local Docker docs with exact startup, token override, model env override, seed/check, and smoke commands.
- [x] 3.2 Document that Docker proves containerized Control Plane/Portal readiness, not host-native Worker Adapter readiness.
- [x] 3.3 Keep model-layer language explicit: Docker control-plane env is not OpenCode/Claude/Codex/Hermes Worker auth.

## 4. Verification

- [x] 4.1 Run `docker-compose config`.
- [x] 4.2 Run the Docker smoke verification path.
- [x] 4.3 Run `openspec validate make-docker-local-run-reliable --strict`.
- [x] 4.4 Run `uv run pytest` after implementation edits.
