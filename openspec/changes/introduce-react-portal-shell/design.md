## Context

AGILE-AI-HTB currently serves the Portal through FastAPI routes and Jinja templates. That has been enough for setup, dashboards, project navigation, board actions, sessions, alarms, and review disposition, and existing specs intentionally avoided a frontend build step for prior readability work.

The TODO list now points beyond page polish: a coding-work cockpit with project/session navigation, planning chat, diff viewing, tool/token maps, richer review evidence, and task status surfaces. Those are client-heavy UI concerns, but the backend contract must stay unchanged: FastAPI owns auth, persistence, estimation, launch guardrails, Worker Runs, token accounting, and review disposition.

## Goals / Non-Goals

**Goals:**

- Add the smallest React/Vite shell that can be served by the existing FastAPI app.
- Migrate only the project workspace plus project board shell first.
- Keep existing Jinja pages working during migration.
- Reuse existing backend functions and task action routes instead of duplicating orchestration logic.
- Make JSON endpoints a thin presentation handoff, not a second product API layer.

**Non-Goals:**

- No Next.js, Remix, SvelteKit, or separate Node server.
- No full Portal rewrite in this slice.
- No drag/drop board, websocket log stream, terminal, file explorer, diff viewer, or chat workspace yet.
- No changes to Worker Adapter semantics, tracking modes, launch guardrails, model routing, budgeting, or review disposition.
- No new database schema unless existing view helpers cannot represent the migrated workspace/board state.

## Decisions

1. **Use React + Vite, served statically by FastAPI.**
   - Rationale: React has the stronger ecosystem for future cockpit widgets such as diff viewers, editor panes, terminals, charts, and multi-panel session UIs. Vite is the smallest boring build tool for this.
   - Alternative considered: Svelte + Vite. Svelte is smaller for pure page polish, but the TODO list points toward cockpit integrations where React saves custom code later.
   - Alternative considered: Next.js/SvelteKit. Rejected because FastAPI is already the backend owner and a second server would add routing/auth/deploy complexity without buying anything needed in the first slice.

2. **Keep FastAPI as the only backend authority.**
   - React renders state and submits actions; FastAPI still validates auth, project binding, estimation, launch guardrails, run automation, review decisions, and token evidence.
   - Existing POST actions may continue to support HTML form redirects while also returning JSON when requested.

3. **Migrate one surface: selected project workspace plus project board shell.**
   - This proves the stack where cockpit work will live: repo identity, board status, task columns, launch/review actions, queue state, and evidence summaries.
   - Existing global/dashboard/setup/session/alarm pages remain server-rendered until a later slice touches them.

4. **Use a thin JSON handoff over existing view helpers.**
   - Add or reuse endpoints such as project workspace state and project board state that return the same data already assembled for templates.
   - Do not create a broad public API, new tables, or parallel orchestration services in this slice.

5. **Package build assets deliberately.**
   - Development may run Vite separately.
   - Production/package mode serves built files from a deterministic static directory.
   - If built assets are missing in development, legacy Jinja routes remain usable; if a React route is requested without assets, FastAPI returns a clear missing-build response instead of a silent broken shell.

## Risks / Trade-offs

- **Risk: Node toolchain increases install friction.** → Mitigate by keeping it isolated under `frontend/`, documenting one build command, and keeping Python/Jinja pages usable during migration.
- **Risk: React duplicates backend rules.** → Mitigate by limiting frontend code to display/form state and testing that launch/review actions still hit existing FastAPI paths.
- **Risk: SPA routing masks auth or 404 behavior.** → Mitigate by only falling back to `index.html` for explicit React-owned routes and preserving FastAPI 404/auth dependencies for data/action endpoints.
- **Risk: First slice grows into a full rewrite.** → Mitigate by excluding chat, diff viewer, terminal, file explorer, websocket streaming, and drag/drop from this change.
