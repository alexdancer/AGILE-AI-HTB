## Context

The portal is a server-rendered FastAPI/Jinja app. It already stores connected repositories in `connected_projects`, detects a project profile, computes Local Runner capability, and has `/settings/project` for connecting a repo. The current landing flow still sends operators to a global dashboard, so the connected repo feels like setup metadata instead of the workspace.

## Goals / Non-Goals

**Goals:**
- Make the normal portal entry feel project-first when a repo is already connected.
- Reuse existing connected project data and Local Runner project connection logic.
- Add a small project overview page with repo identity, profile, readiness, and links to existing workflows.
- Keep implementation server-rendered and dependency-free.

**Non-Goals:**
- No project-scoped board, session, report, or alarm queries in this slice.
- No schema migration or new `project_id` columns.
- No SPA, file picker, websocket updates, or dashboard redesign.
- No changes to Worker Adapter identity, tracking modes, model routing, or launch semantics.

## Decisions

1. **Reuse `connected_projects` as the workspace source.**
   - The table already has the repo name, root path, profile JSON, capability JSON, and update ordering.
   - Alternative considered: add a workspace table. Rejected as duplicate state.

2. **Add project routes without changing existing global routes.**
   - `/projects` lists connected repos and offers the same open/connect form.
   - `/projects/{project_id}` shows the project overview.
   - Existing `/dashboard`, `/board`, `/sessions`, `/alarms`, and settings pages remain valid.
   - Alternative considered: immediately move every page under `/projects/{id}`. Rejected as too much scope for the first UX correction.

3. **Redirect login to the most recently connected project when available.**
   - This makes the portal feel like it opens into the last repo.
   - If no project exists, redirect to `/projects` so the first action is opening a repo.
   - Alternative considered: keep `/dashboard` as the default. Rejected because it preserves the generic-console feel this change is fixing.

4. **Use links, not duplicated controls, on the project overview.**
   - The overview links to `/board`, `/sessions`, `/settings/workers`, and `/settings/project`.
   - It may show counts/readiness derived from existing data, but actions remain on existing pages.
   - Alternative considered: embed board/session/settings forms on the overview. Rejected as duplicated UI.

## Risks / Trade-offs

- Project overview links to global board/sessions for now, which can still show unrelated items. → Mitigate with clear copy and defer scoped filtering until it demonstrably matters.
- Login redirect changes operator muscle memory. → Keep global dashboard reachable from navigation.
- Multiple connected projects need a simple switch path. → `/projects` remains the explicit project picker.
