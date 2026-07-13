## Context

The staged React migration has completed and archived separate parity changes for Portal chrome, Dashboard, project workspace, and the governed AGILE Board lifecycle. FastAPI still routes root, successful login, and auth-disabled login/logout through `_default_portal_landing()`, which always chooses a Jinja project route. React build validation already exists in `react_shell.py`: `_react_index()` accepts only an index whose referenced `/static/react/*` assets all exist, while explicit `/app` requests return a clear `503` when that validation fails.

This change is a routing promotion, not another surface migration. Sessions, Alarms, Setup, Settings, task history, reports, and Task Breakdown Review remain authoritative Jinja pages reached through ordinary full-page links from the React shell.

## Goals / Non-Goals

**Goals:**

- Make `/app` the normal post-auth and auth-disabled local Portal landing only when the complete built shell is available.
- Reuse one build-readiness decision for root, login, and no-auth logout routing.
- Preserve the current Jinja project landing as an automatic default fallback for missing or partial React builds.
- Preserve authentication, cookie, deep-link, and non-migrated Jinja workflow behavior.
- Prove the promotion with exact route tests plus a built-app browser smoke through Dashboard, workspace, board, and Jinja fallback links.

**Non-Goals:**

- Migrating Sessions, Alarms, Setup, Settings, task history, reports, Task Breakdown Review, or login UI to React.
- Removing Jinja Dashboard, project workspace, board, or fallback routes.
- Changing React route ownership beyond `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board`.
- Changing auth, persistence, API payloads, governance, Worker Adapters, token accounting, or frontend dependencies.

## Decisions

### Use the existing complete-build validator as the promotion gate

Expose a small build-readiness helper from `react_shell.py` that delegates to the existing index-and-referenced-assets validation. The Portal landing helper returns `/app` only when that helper succeeds; otherwise it returns the current first-project-or-`/projects` Jinja landing.

Alternative: redirect every authenticated operator to `/app` and let the shell return `503`. Rejected because the default landing must remain usable when packaged assets are absent or partial.

Alternative: duplicate file checks in `portal.py`. Rejected because route serving and landing promotion could drift on what counts as a complete build.

### Keep one build-aware landing helper for every successful entry path

Root after authentication, successful auth-required login, auth-disabled `/login`, auth-disabled login POST, and auth-disabled logout use the same helper. Unauthenticated auth-required root still redirects to `/login`; auth-required logout still redirects to `/login`.

Alternative: change only root and successful login. Rejected because local no-auth entry/logout would retain inconsistent Jinja-first behavior.

### Promote only the front door

`/app` becomes the default dashboard, but existing Jinja routes remain addressable and React links to non-migrated workflows remain full-page anchors. Explicit React deep links retain their current build-safe `503` response; only automatic landing selection falls back before sending the operator there.

Alternative: redirect Jinja `/dashboard`, `/projects`, or project-board routes into React. Rejected because those routes are fallback and compatibility surfaces, and redirecting them could trap operators when assets fail.

### Make route and smoke evidence executable

Backend tests cover the build matrix for auth-required and auth-disabled root/login/logout paths, including valid cookie, no projects, connected projects, missing index, and missing referenced assets. Existing explicit `/app` missing-build and unknown-route tests remain. Built-app smoke loads the default root, confirms React Dashboard and chrome, enters a project workspace and board, then follows at least one ordinary Jinja fallback link.

Source-string assertions alone are insufficient because default routing, asset availability, client navigation, and full-page fallback ownership must execute.

## Risks / Trade-offs

- [Stale or partial packaged assets could redirect operators into a broken shell] → Reuse `_react_index()` and require every referenced local React asset before selecting `/app`.
- [A circular route-module import could make startup fragile] → Expose a dependency-light readiness helper from `react_shell.py`; keep its existing lazy Portal import inside the dashboard endpoint and add app-import/startup coverage.
- [Operators could lose access to non-migrated workflows] → Keep Jinja routes unchanged, retain ordinary anchors, and smoke-test one fallback navigation.
- [Default behavior changes only when build output exists, making environments differ] → Specify the build-aware behavior explicitly and test both built and unbuilt states.

## Migration Plan

1. Add and test the shared React build-readiness/landing decision.
2. Switch successful root/login/no-auth logout paths to the build-aware landing helper.
3. Run backend, frontend build, strict OpenSpec, and browser-smoke gates.
4. Roll back by restoring the Jinja-only landing helper; no data or schema migration is required.

## Open Questions

None.
