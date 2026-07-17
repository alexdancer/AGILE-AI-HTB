## Why

The Portal is moving from a readable server-rendered admin surface toward a coding-work cockpit with project context, board operations, review evidence, diffs, token maps, and planning/chat surfaces. The current FastAPI/Jinja stack is still the right backend owner, but it is becoming the wrong place to build richer client-side cockpit interactions.

## What Changes

- Add a Vite React frontend as an optional Portal shell served by the existing FastAPI app.
- Mount the built React assets from FastAPI while keeping existing Jinja pages available during migration.
- Migrate the first React surface narrowly: the project workspace plus project board shell for one selected project.
- Expose only the authenticated JSON endpoints needed by that first React surface, reusing existing board/workspace data and task action paths.
- Preserve FastAPI ownership of auth, task creation, estimation, launch guardrails, Worker Runs, budget governance, review disposition, and persistence.
- Update the Portal quality contract so this frontend-refactor slice may introduce a frontend build step without rewriting all Portal pages.
- Do not introduce Next.js, SvelteKit, a separate Node server, a UI mega-framework, websocket streaming, drag/drop Kanban, diff viewer, terminal, file explorer, or chat workspace in this first slice.

## Capabilities

### New Capabilities
- `react-portal-shell`: React/Vite Portal shell behavior, FastAPI static serving, first migrated project workspace/board surface, and JSON handoff boundaries.

### Modified Capabilities
- `portal-quality-system`: Allow this explicit frontend-refactor slice to introduce a Vite/React build step while preserving existing server-rendered pages during migration.

## Impact

- Adds a small Node/Vite toolchain for frontend build and development.
- Adds a `frontend/` source tree and packaged/static build output handling.
- Updates FastAPI app startup/routing to serve built React assets when present.
- Adds or reuses authenticated JSON endpoints for project workspace and project board state.
- Updates packaging/tests so Python-only installs still fail clearly or skip React serving when frontend assets are absent in development.
- Keeps existing Jinja templates, routes, and tests as the fallback/migration baseline.
