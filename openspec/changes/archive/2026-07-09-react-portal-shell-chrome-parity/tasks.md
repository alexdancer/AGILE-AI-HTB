## 1. Backend: authenticated sidebar nav endpoint

- [x] 1.1 In `src/agile_ai_htb/routes/react_shell.py`, add `GET /api/portal/nav` with `Depends(require_portal_auth)`. It SHALL call `portal_template_context(request)` (imported from `agile_ai_htb.template_context`) and return `{portal_auth_required: bool, sidebar_projects: [{id, name, task_count}, ...]}`, trimming any keys the sidebar does not need. No new domain logic, no mutation paths.
- [x] 1.2 In `tests/portal/test_react_shell.py`, add `test_portal_nav_requires_auth` (auth required + no cookie → 401/403) and `test_portal_nav_shape` (auth + connected project → 200 with `portal_auth_required` boolean and `sidebar_projects` items containing `id`, `name`, `task_count`; `No projects` case returns an empty array). Reuse `tests/portal/helpers.py` (`_client`, `_connect_project`, `_portal_headers`, `PORTAL_TOKEN`).

## 2. Frontend: Shell + sidebar + footer chrome

- [x] 2.1 Rewrite `frontend/src/components/Shell.jsx` to render the Jinja `base.html` frame:
  - `<div class="shell">` grid (`grid-template-columns: 220px 1fr; grid-template-rows: auto 1fr auto; min-height: 100vh`) so the in-shell footer occupies the third row.
  - `<header class="topbar">` with `<div class="brand">AGILE-AI-HTB<span class="dot">·</span>Portal</div>` (brand links to `/app` via AppLink).
  - `<aside class="sidebar">` containing:
    - `Projects` group heading.
    - Project list from `useResource("/api/portal/nav")`: each project is an `AppLink` to `/app/projects/{id}` with `.project-item` (+ `active` when `activeProjectId === project.id`), `.project-name`, `.project-sub` (`Task board` when `project.task_count` else `No tasks`), and a `.project-board` `AppLink` to `/app/projects/{id}/board` rendered only when `project.task_count`.
    - `No projects` empty state and `+ Open local repo` `sidebar-action` link to `/projects`.
    - `Setup` group with `First-run setup` link to `/setup`.
    - `Governance` group with `Dashboard`, `Sessions`, `Alarms` full-page `<a>` links.
    - `Planning` group (only after a successful response with `sidebar_projects.length === 0`) with `Task board` full-page `<a>` to `/board`; loading and error states do not impersonate a successful empty response.
    - `Settings` group with `Control plane model`, `Token budget`, `Projects`, `Worker adapters` full-page `<a>` links.
    - Logout form (POST `/logout`, `class="logout"`) only when `portal_auth_required` is true.
  - `<main class="main">{children}</main>`.
  - `<footer>AGILE-AI-HTB portal · operator-controlled budget governance</footer>`.
  - Accept `activeView` and `activeProjectId` props from the parent (App.jsx) for active-state highlighting.
- [x] 2.2 Pass `activeView` and `activeProjectId` from `App.jsx` down to `Shell.jsx` in every view (Home, Workspace, Board). `parseRoute` already produces the needed values; App.jsx maps `view` and `projectId` into props.
- [x] 2.3 Update Home.jsx, Workspace.jsx, and Board.jsx so they pass the new props through to `Shell` (or so `Shell` receives them from App and wraps the views — whichever matches the existing wiring). Do not change any data fetching, action forms, or project-picker behavior; only the `Shell` invocation changes.
- [x] 2.4 Non-migrated Jinja links in the sidebar (`/setup`, `/dashboard`, `/sessions`, `/alarms`, `/settings/control-plane`, `/settings/budget`, `/settings/project`, `/settings/workers`, `/board`, `/projects`) MUST render as ordinary `<a href>` tags (no `AppLink`), per the plan's implementation rule. React-owned routes (`/app`, `/app/projects/:id`, `/app/projects/:id/board`) keep using `AppLink`.

## 3. Frontend CSS parity

- [x] 3.1 In `frontend/src/tokens.css`, mirror `base.html`'s layout values for `.topbar`, `.brand`/`.brand .dot`, `.sidebar`, `.sidebar nav`, `.sidebar a` (active/hover), `.group`, `.project-list`, `.project-item`/`.project-name`/`.project-sub`/`.project-board`/`.sidebar-action`/`.sidebar-empty`, `.logout`/`.logout button`, and `.main`. Use `.shell-footer` plus a third `auto` grid row because React keeps the footer inside `.shell`; retain the same footer visual values and shared `:root` variables.
- [x] 3.2 Responsive `@media (max-width: 900px)` rule collapses `.shell` to one column and places the React main/footer in rows 3/4, preserving Jinja's mobile layout with the explicit footer row.

## 4. Tests for chrome parity

- [x] 4.1 In `tests/portal/test_react_shell.py`, add frontend source-contract assertions (string presence in built shell or JSX source) that assert the shell renders:
  - `Projects` group, `+ Open local repo`, `First-run setup`, `Dashboard`, `Sessions`, `Alarms`, `Control plane model`, `Token budget`, `Worker adapters`, `AGILE-AI-HTB portal · operator-controlled budget governance`.
  - Logout form posts to `/logout`.
  - `Task board` / `No tasks` subtitle contract.
  - `.project-board` link to `/app/projects/{id}/board` only when a project has tasks.
- [x] 4.2 Render the exported sidebar through Vite SSR and assert the active project, board-only sublink, home action, loading/error/empty, logout, and conditional task-board behavior without adding a DOM library dependency.

## 5. Verify

- [x] 5.1 `openspec validate react-portal-shell-chrome-parity --strict` → "Change 'react-portal-shell-chrome-parity' is valid"
- [x] 5.2 `npm --prefix frontend run check` → builds successfully
- [x] 5.3 `uv run pytest tests/portal/test_react_shell.py -q` → all pass, including new nav/chrome tests
- [x] 5.4 `uv run pytest -q` → full suite green
- [x] 5.5 `git diff --check` → clean
- [x] 5.6 Update task checkboxes to `- [x]` only after each verification passes.

## 6. Review remediation

- [x] 6.1 Restrict FastAPI shell serving and client parsing to `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board`; return 404 for unknown or extra-segment paths.
- [x] 6.2 Add executable frontend rendering tests for loading, error, empty, active-project, board-only sublink, logout, and conditional task-board states.
- [x] 6.3 Fix the home active state and ensure Planning/`No projects` render only after a successful empty nav response.
- [x] 6.4 Align the delta design/spec, main React capability spec, and frontend README with explicit route ownership, board-only sublink highlighting, and Jinja remaining the default landing.
- [x] 6.5 Re-run targeted frontend/backend tests, frontend build, strict OpenSpec validation, full pytest, diff checks, and independent review before marking remediation complete.