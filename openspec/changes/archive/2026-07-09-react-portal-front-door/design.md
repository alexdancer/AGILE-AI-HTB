## Context

`introduce-react-portal-shell` added a React/Vite shell served by FastAPI that
owns the project workspace and board at `/app/*`, with JSON handoff endpoints
and a build-missing fallback. The shell is functionally correct but has no
entry point: the authenticated landing still resolves to Jinja
(`_default_portal_landing` → `/projects` or `/projects/<id>`), and the React
shell has no home or project picker, so the only way in is a hand-typed
`/app/projects/<id>` URL.

The end goal is a fully React Portal. That is a multi-slice program: porting the
remaining ~dozen Jinja surfaces, converting ~59 guarded POST action routes from
Jinja redirects to JSON, then deleting Jinja and making the build mandatory.
This change is the first slice and is scoped strictly to reachability so the
existing React surfaces become usable immediately without taking on the
migration's risky write-path and guardrail work.

## Goals / Non-Goals

**Goals:**

- Operators enter the React shell by logging in and clicking, never by typing a
  URL or a project id.
- A missing frontend build must never brick the Portal during migration.
- Reuse existing project-list and task-count data; add no new tables and no new
  orchestration logic.

**Non-Goals:**

- No new migrated read surfaces beyond the existing workspace/board.
- No conversion of POST actions to JSON; Jinja redirects stay authoritative.
- No deletion of Jinja and no build-mandatory posture yet.
- No React login/auth rewrite; the Jinja login page stays.

## Decisions

1. **Build-aware front door.**
   - The authenticated landing prefers the React shell (`/app`) when the built
     frontend is present and falls back to the existing Jinja landing when it is
     absent. Root redirect and post-login redirect both use this resolution.
   - Rationale: flipping the front door is a one-place change and fully
     reversible, but making it build-conditional preserves the Jinja safety net
     until the final migration slice makes the build mandatory.
   - Alternative considered: unconditional flip to `/app`. Rejected for now
     because a missing/broken build would take down the whole Portal while other
     surfaces are still Jinja.

2. **Keep Jinja login; it lands in the build-aware landing.**
   - Login remains the server-rendered form that sets the existing signed cookie,
     then redirects to the build-aware landing (React when built). The same
     cookie authorizes React shell routes and JSON endpoints, so no auth change
     is needed.

3. **Project picker over a thin project-list JSON endpoint.**
   - Add an authenticated `GET` JSON endpoint returning the connected projects
     with their task counts, derived from the same helpers that feed the Jinja
     projects page and sidebar. No new schema, no parallel API.
   - The React home renders that list with links into each project's React
     workspace and board, and an empty state linking to the existing
     connect-project flow so it is never a dead end.

4. **Client-side navigation via the History API.**
   - The React shell navigates between home, workspace, and board using
     `history.pushState` + `popstate`, so movement needs no full reloads or typed
     URLs. Deep links and refreshes on any `/app/*` path still work because
     FastAPI already serves the shell index for every `/app/*` route.
   - Links that target non-migrated Jinja surfaces remain ordinary full-page
     navigations.

## Risks / Trade-offs

- **Risk: missing build bricks the Portal after the front-door flip.** → Mitigate
  by making the landing build-aware with a Jinja fallback; only the final
  migration slice removes the fallback and makes the build mandatory.
- **Risk: default-UX change affects every operator at once.** → Mitigate by the
  fallback and by the flip being a single reversible resolution point.
- **Risk: client-side routing masks auth/404 behavior.** → Mitigate by keeping
  auth on JSON endpoints and shell routes, only using client routing within
  `/app/*`, and leaving Jinja links as full navigations.
- **Trade-off: two navigation systems coexist during migration.** Accepted: the
  React shell is the front door, Jinja surfaces are reachable leaves, until later
  slices port them.
