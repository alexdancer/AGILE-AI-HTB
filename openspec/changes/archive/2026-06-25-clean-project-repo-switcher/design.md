## Context

The portal already has project workspace routes and project-scoped board routing. Connected projects are stored and rendered through existing project view models, but project switching is not a first-class navigation pattern. The current sidebar only shows the active project when one is supplied by the route, and settings still exposes repo selection as "Connected project".

## Goals / Non-Goals

**Goals:**

- Make connected repositories visible and switchable from the sidebar, similar to Codex's project list.
- Preserve existing `/projects`, `/projects/{project_id}`, and `/projects/{project_id}/board` behavior.
- Keep the change template-only or route-context-light where possible.
- Use existing connected project records and project view models.

**Non-Goals:**

- No new project/workspace schema.
- No SPA, websocket, drag/drop, or file picker.
- No project-scoped sessions/reports/dashboard in this slice.
- No Worker Adapter, model, tracking-mode, or launch semantics change.

## Decisions

1. **Use existing connected projects as sidebar data.**
   - Rationale: the data already exists and is enough for repo switching.
   - Alternative rejected: add a new workspace table or recent-project model. That is extra state without a proven need.

2. **Make the sidebar the switcher.**
   - Rationale: this matches the Codex-style mental model: choose repo first, then work inside it.
   - Alternative rejected: only improve `/projects`. That still hides switching one click away from every workflow page.

3. **Route project clicks to the overview, with board as the scoped work entry.**
   - Rationale: overview already owns repo identity/readiness; board remains the task workflow.
   - Alternative rejected: route every sidebar project directly to the board. That skips readiness/profile context for newly opened repos.

4. **Prefer copy changes over new controls.**
   - Rationale: replacing "Connected project" with "Projects" / "Open local repo" fixes the operator-facing language without changing backend semantics.

## Risks / Trade-offs

- Sidebar can get long with many repos → keep simple list now; add search/collapse only after real repo count pain.
- Global pages may not know the active project → show the repo switcher regardless, and highlight only when route context provides an active project.
- Passing project navigation context to all templates may touch several routes → use one small shared context helper if needed, not per-route bespoke code.
