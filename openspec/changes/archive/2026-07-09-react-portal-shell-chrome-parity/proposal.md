## Why

The React `/app` shell renders a topbar-only layout (centered content, flat nav
links) that looks like a different product from the Jinja Portal. Jinja
`base.html` ships a full app frame — top brand, sidebar with project list,
Setup/Governance/Planning/Settings groups, logout, footer, active-state
highlighting — and the React shell lacks every one of those. Before any more
React surfaces are added (Phase 3 dashboard, Phase 4 board parity), the shell
must feel like the same app so operators are not bounced between two layouts.
This is Phase 2 of `docs/REACT_PORTAL_PARITY_PLAN.md`.

## What Changes

- Replace the topbar-only `Shell.jsx` with the Jinja `base.html` layout
  contract: a `220px 1fr` grid with a top brand bar, left sidebar, and main
  content region.
- Port the sidebar structure verbatim from `base.html`:
  - `Projects` group with connected projects (`Task board` / `No tasks`
    subtitle), `└ Task board` sub-link when a project has tasks, and
    `+ Open local repo` action.
  - `Setup` group with `First-run setup`.
  - `Governance` group with `Dashboard`, `Sessions`, `Alarms`.
  - `Planning` group shown only when no projects are connected, linking the
    unscoped `/board`.
  - `Settings` group with `Control plane model`, `Token budget`, `Projects`,
    `Worker adapters`.
  - `Logout` form (POST `/logout`) only when portal auth is required.
- Add a footer (`AGILE-AI-HTB portal · operator-controlled budget governance`)
  so the React frame matches Jinja end-to-end.
- Add active navigation state to the sidebar: the current project and current
  group/route are highlighted identically to Jinja's `active_page` /
  `active_project` contracts.
- Non-migrated pages (Dashboard, Sessions, Alarms, Setup, all Settings, task
  history, full board) remain ordinary full-page anchors from React chrome.
  React-owned routes (`/app`, `/app/projects/:id`,
  `/app/projects/:id/board`) use client-side navigation already provided by
  `AppLink`/`NavContext`.
- Add a thin authenticated JSON endpoint that reuses the existing
  `portal_template_context` helper so the sidebar projects list and
  `portal_auth_required` flag come from the same single source of truth Jinja
  uses — no parallel project helpers, no duplicated counts.
- `/app` stays non-default. Route ownership is tightened to `/app`,
  `/app/projects/:id`, and `/app/projects/:id/board`; unknown or extra-segment
  `/app/*` paths return 404 instead of silently rendering Home. No dashboard,
  board workflow, budget, or review rule changes. No new UI link to `/app` from
  the default Jinja Portal.
- Frontend visual tokens are already shared (`tokens.css` mirrors `base.html`
  `:root`); this change adds the missing layout/sidebar/footer CSS to
  `tokens.css` so the React frame reads as the same surface.

**Non-breaking for declared routes** (no supported route/endpoint removed or
renamed): `/app`, `/app/projects/:id`, `/app/projects/:id/board`,
`/api/projects`, `/api/projects/{id}/workspace`, `/api/projects/{id}/board`, the
503 missing-build response, and every Jinja page remain available. The previous
undeclared catch-all behavior for other `/app/*` paths is intentionally removed.
React remains reachable at `/app` and is still not the default landing.

## Capabilities

### New Capabilities
<!-- None. This change extends an existing capability; it introduces no new one. -->

### Modified Capabilities
- `react-portal-shell`: add a requirement that the React shell preserves the
  full Portal chrome (sidebar, groups, project list, logout, footer, active
  state) so `/app` reads as the same product as the Jinja Portal, and clarify
  that only the three declared React routes receive the shell. Existing
  requirements for build-aware serving, JSON handoff, and project picker are
  otherwise unchanged.

## Impact

- **Frontend:** `frontend/src/components/Shell.jsx` rewritten to render the
  Jinja-equivalent grid + sidebar + footer; new sidebar/nav subcomponents under
  `frontend/src/components/`; `frontend/src/tokens.css` gains the missing
  `.shell`/`.sidebar`/`.group`/`.project-item`/`.project-board`/footer layout
  rules. Visual values mirror `base.html`; React adds an explicit footer row
  because its footer remains inside `.shell`.
- **Backend:** one new authenticated JSON endpoint in
  `react_shell.py` (e.g. `/api/portal/nav`) returning
  `{portal_auth_required, sidebar_projects}` derived from
  `portal_template_context`, plus explicit shell routes replacing the broad
  `/app/{path}` catch-all. No schema, new domain logic, or mutation paths.
- **Tests:** backend tests cover nav auth/shape and exact route ownership;
  executable Vite SSR tests render sidebar loading, error, empty, auth, and
  active-state variants. Static source checks remain only for fixed copy and
  ordinary Jinja anchor contracts.
- **Frontend build:** `npm --prefix frontend run check` stays green.
- **APIs:** one new read-only GET endpoint. Existing JSON endpoints are
  unchanged; shell serving is narrowed to the three declared React routes.
- **References:** `docs/REACT_PORTAL_PARITY_PLAN.md` Phase 2; archived
  `react-portal-front-door` and completed `react-portal-default-rollback`
  precede this change.