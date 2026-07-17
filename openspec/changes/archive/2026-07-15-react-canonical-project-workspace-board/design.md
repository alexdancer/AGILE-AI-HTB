## Context

Slice 11a applied the inversion pattern to `/dashboard` and `/projects`: the canonical GET checks the React build first, serves the shell when it is complete, and renders the existing Jinja page otherwise. This change applies the same rule to the last two React-owned surfaces, `/projects/{project_id}` and `/projects/{project_id}/board`.

Almost everything needed already exists:

- `GET /api/projects/{project_id}/workspace` (`react_shell.py:645`) and `GET /api/projects/{project_id}/board` (`react_shell.py:809`) are authenticated, bounded, and specified.
- `Workspace.jsx` and `Board.jsx` are complete surfaces with archived handling, and `App.jsx` already routes both under `/app`.
- The launch, queue, review, archive, dismiss, and Restore actions already negotiate JSON outcomes for React callers (27 negotiation sites in `portal.py`), so React never round-trips through the `?error=` redirects those routes use for HTML callers.

The net-new work is therefore not a view. It is route selection plus finishing the canonical URL ownership that 11a deliberately deferred: the `/app/projects/{id}` target is currently baked into card links, FastAPI's projected workspace hrefs, and sidebar highlighting.

## Goals / Non-Goals

**Goals:**

- `/projects/{project_id}` and `/projects/{project_id}/board` select React when the complete build is available and the existing Jinja page when it is missing or partial.
- The backend's unknown-project `404` and archive checks stay authoritative and are decided before the shell is served.
- Every in-shell project target — card links, projected `board_href`, Restore `next_href`, sidebar highlighting — uses the canonical URL, so the retirement change only deletes.
- The React project surfaces stop offering server-rendered escape links and sanitize their error branches.

**Non-Goals:**

- Making `/app/projects/{id}` or `/app/projects/{id}/board` redirects, or deleting any Jinja template — the final retirement change owns both, together.
- `/board`, the redirect shim onto the first connected project's board.
- Login and the Portal Recovery Surface (slice 10).
- New mutations, schema, JSON endpoints, or changes to launch/estimation/budget/archive semantics.
- Unifying error-handling tiers across views this change does not touch.

## Decisions

### 1. Validate first, then serve the shell

`/projects/{project_id}` and `/projects/{project_id}/board` both look up the project and can `404`. `/projects/{project_id}/board` additionally redirects archived projects. Checking `_react_index()` first would turn an unknown project into a `200` shell that discovers the `404` only after the JSON handoff — moving a backend-authoritative decision into the browser.

The build-aware check therefore goes *after* the existing lookup, matching the precedent `project_task_history` already set (`portal.py:712-726`): resolve the project, keep every existing guard, then choose renderer. This differs from 11a's dashboard, where the check goes first precisely because that route has nothing to validate.

### 2. Archived boards serve the shell when the build is available

Jinja redirects an archived project's board to `/projects/{id}?error=Restore this archived project…` (`portal.py:667`). Two options existed: keep that redirect in both build states, or serve the shell and let React render its archived board.

Chose serve-the-shell. React's archived-board state is already specified and implemented — it identifies the archived state and routes to Restore — so the guard is preserved, not dropped; only the mechanism differs. Keeping the redirect would instead require React's Workspace to parse and sanitize a `?error=` query param it never reads today, and would leave the spec'd React archived-board view reachable only through the `/app` alias, making it dead code at retirement.

The Jinja fallback keeps the redirect unchanged for the missing/partial build, where React is not there to render the equivalent. Both paths are pinned by scenarios.

### 3. Canonical ownership extends to projected hrefs and sidebar state

`/app/projects/{id}` is not only in card links. FastAPI projects `board_href` and board-targeting attention hrefs as exactly `/app/projects/{project_id}/board`, the Restore success outcome returns `next_href: /app/projects/{project_id}`, and the sidebar highlights on `/app` paths. Those are spec'd exactly and asserted by tests.

Leaving them would mean the shell navigates to aliases while the canonical routes it just claimed sit unused, and retirement — which flips `/app` to a redirect — would turn every project card click into a redirect hop. All of them move to the canonical URL in this slice. `/app/*` keeps resolving for existing deep links and bookmarks; it simply stops being anything's target.

### 4. Sidebar highlighting matches both canonical and alias routes

Highlighting keys off the current path. Since `/app/projects/{id}` still resolves, the sidebar must highlight for both shapes until retirement, not just the canonical one — otherwise an operator on a bookmarked `/app` deep link loses their place in the sidebar. The scenario is written against both.

### 5. Escape links go, following 11a's Decision 7

`Board.jsx:138`, `Workspace.jsx:92`, and `TaskHistory.jsx:83` each link to their server-rendered equivalent. Once the canonical URL is React, those links point at a fallback rather than a destination, and after retirement they point at nothing. They are removed, and those branches adopt the established per-view `safeError` local rather than raw `error.message` — the same treatment 11a applied to the dashboard, and the same deliberate duplication over a shared import (`Setup.jsx:5`, `Sessions.jsx:6`, `Alarms.jsx:27`, `Projects.jsx:7`).

`TaskHistory.jsx` is included even though its route migrated in an earlier slice: it is the same defect, its escape link points at the same kind of fallback, and its error branch is already being read here.

## Risks / Trade-offs

- **The `?error=` redirects still exist for HTML callers** → Verified non-reachable from React: the launch, queue, and review actions negotiate JSON (`_wants_react_json`) before falling back to redirect, so React consumes outcomes inline. If a future action skips negotiation, its error would land on a React surface that ignores the query param and silently swallow it. The archived-board scenario pins the one redirect that survives, and it is Jinja-only.
- **Behavior at the archived board differs by build state** → Redirect under Jinja, rendered archived state under React. That asymmetry is inherent to build-aware selection and is what Decision 2 accepts deliberately; both are specified rather than incidental.
- **Moving projected hrefs breaks exact-href tests** → Intended. Those assertions are the contract; they move with it. The risk is missing one, so the routing work is verified by an executable matrix rather than by inspection.
- **`/app` and canonical both render the same surfaces until retirement** → Bounded and specified as an alias, exactly as `/app` and `/dashboard` have coexisted since 11a. Retirement owns the collapse.
- **A vacuous test is the standing hazard here** → 11a's accuracy fix had to be mutation-checked because slice 9 shipped a test that passed against the old template. The escape-link and href-move tests must fail against the current tree before they count.

## Migration Plan

No data migration. Deployment is the existing build-aware selection, so rollback is reverting the route changes; the Jinja pages remain in place and unmodified throughout this slice.

## Open Questions

None. The archived-board disposition (Decision 2) and the canonical-ownership scope (Decision 3) were both settled before this change was drafted.
