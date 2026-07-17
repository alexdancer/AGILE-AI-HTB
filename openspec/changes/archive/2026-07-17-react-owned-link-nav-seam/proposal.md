## Why

The React Portal shell has two navigation primitives — `AppLink` (unconditional client-side navigation) and raw `<a>` (full-page navigation) — and no shared rule for choosing between them. The correct route-aware primitive already exists as `OwnedLink` + `isReactOwnedPath`, but it is trapped as a private helper inside `TaskBreakdownReview.jsx`, and its ownership predicate is a second, hand-maintained copy of the route list that `App.parseRoute` already owns. Every other view therefore hand-picks `AppLink` vs `<a>` per anchor, and the persistent sidebar's Settings/Alarms links still perform full-page reloads of routes that React now owns — a stale carryover from when those surfaces were server-rendered.

## What Changes

- Extract `parseRoute` from `App.jsx` into a dependency-free `frontend/src/routes.js`, imported by both `App.jsx` and `nav.jsx` (breaks the `nav.jsx` → `App.jsx` import cycle).
- Promote `OwnedLink` and `isReactOwnedPath` from `TaskBreakdownReview.jsx` into `nav.jsx` as the shared route-aware link seam. Re-derive `isReactOwnedPath` from `parseRoute` so the router is the single source of truth for "what React owns" (no parallel regex to drift).
- `TaskBreakdownReview.jsx` deletes its local `OwnedLink`/`isReactOwnedPath` copies and imports the shared ones.
- Migrate the class-1 static internal anchors to `OwnedLink`: the sidebar `Settings` group and `+ Open local repo` (`Shell.jsx`), and Dashboard's `/sessions`, `/sessions/{id}`, `/alarms`, and `/settings/project` literals (`Dashboard.jsx`). React-owned targets become in-shell; the primitive leaves any non-React target as a full-page anchor by construction.
- **BREAKING (spec behavior)**: the sidebar `Settings` group links change from full-page to in-shell client-side navigations because they now resolve to React-owned routes. This also reverses the ratified "Full-page sidebar links remain full-page navigations" requirement for `Alarms`, whose code already navigates in-shell (`AppLink`) ahead of that requirement; no `Alarms` code change is needed. The reversal applies to React-owned targets only.
- Explicitly unchanged full-page anchors: `/login`, `/logout`, the bare `/board` Planning shim, Board's deliberate "Server board" comparison link, and all error-recovery "Retry" links (which intentionally re-bootstrap).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `react-portal-shell`: reverse the requirement that sidebar Settings/Alarms links remain full-page navigations — for React-owned targets they SHALL navigate in-shell via the shared route-aware link seam; genuinely server-rendered targets (`/login`, `/logout`, bare `/board`) remain full-page. Update the sidebar navigation-groups scenario wording accordingly.

## Impact

- Frontend only. New file `frontend/src/routes.js`; edits to `frontend/src/App.jsx`, `frontend/src/nav.jsx`, `frontend/src/components/Shell.jsx`, `frontend/src/views/Dashboard.jsx`, `frontend/src/views/TaskBreakdownReview.jsx`.
- No backend, FastAPI route, JSON handoff, schema, or auth changes. No new dependencies.
- Tests: `frontend/tests/shell.test.mjs` — `parseRoute` import moves to `routes.js`; add coverage for the shared `OwnedLink`/`isReactOwnedPath` (React route → client nav, server/unknown path → full-page `<a>`) and for the reversed sidebar navigation behavior.
- Out of scope: class-2 server-provided href anchors (`action.href`, `links.*_href`, `session_href`, etc.), the `useResource` data-loading consolidation (separate candidate), and Board filter performance (separate candidate).
