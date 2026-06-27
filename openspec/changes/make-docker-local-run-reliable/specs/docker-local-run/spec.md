## ADDED Requirements

### Requirement: Docker Compose local Control Plane runtime
The system SHALL provide a Docker Compose local runtime that builds and starts the AGILE-AI-HTB Control Plane/Portal as a single app service.

#### Scenario: Start local Docker service
- **WHEN** an operator runs the documented Docker Compose startup command from the repo root
- **THEN** the system SHALL build the local AGILE-AI-HTB image
- **AND** expose the Portal/API on host port 8000

#### Scenario: Health endpoint succeeds
- **WHEN** the Docker service is running
- **THEN** `GET /health` on the published port SHALL return a successful health response

#### Scenario: Login page is reachable
- **WHEN** the Docker service is running
- **THEN** `GET /login` on the published port SHALL return the Portal login page

### Requirement: Docker SQLite persistence
The Docker runtime SHALL persist AGILE-AI-HTB SQLite state outside the container filesystem.

#### Scenario: Default database path uses data volume
- **WHEN** the Docker service starts with default Compose settings
- **THEN** the effective database path SHALL be `/data/harness.db`
- **AND** `/data` SHALL be backed by a persistent Docker volume

#### Scenario: Demo seed writes persisted database
- **WHEN** an operator runs `htb seed-demo` inside the Docker service
- **THEN** demo task data SHALL be written to `/data/harness.db`

### Requirement: Docker guardrails path
The Docker runtime SHALL make the repository guardrails configuration available inside the container at the app's configured guardrails path.

#### Scenario: Guardrails mounted read-only
- **WHEN** the Docker service starts from the repo root
- **THEN** `guardrails.yaml` SHALL be available inside the container at `/app/guardrails.yaml`
- **AND** the Compose mount SHALL be read-only

### Requirement: Docker smoke verification path
The repo SHALL provide a documented runnable Docker smoke verification path.

#### Scenario: Smoke verification checks runtime
- **WHEN** Docker is available and the operator runs the Docker smoke verification path
- **THEN** it SHALL verify image build/start, `/health`, `/login`, `htb seed-demo`, and `/data/harness.db` existence
- **AND** it SHALL recreate the service before rechecking `/data/harness.db` so persistence is proven outside the removed container filesystem
- **AND** it SHALL clean up the started service after the check

#### Scenario: Compose command portability
- **WHEN** the operator's machine may provide either Compose command shape
- **THEN** the smoke verification path SHALL use `docker-compose` when available
- **AND** fall back to `docker compose` otherwise

### Requirement: Docker Worker Adapter boundary
Docker documentation SHALL distinguish containerized Control Plane readiness from host-native Worker Adapter readiness.

#### Scenario: Host Worker access not implied
- **WHEN** an operator reads Docker setup documentation
- **THEN** the documentation SHALL state that Docker startup does not automatically provide access to host-installed OpenCode, Claude Code, Codex, Hermes, host repo paths, or host credentials
- **AND** Worker launch readiness SHALL remain governed by configured Worker Adapter and tracking-mode checks
