## Context

Phase 5 slices 1–9 established a repeatable inversion pattern: a canonical GET checks the React build first and serves the shell when it is complete, otherwise renders the existing Jinja page at the same URL. Dashboard, Projects, project workspace, and Board predate that rule and never took their canonical URLs — they are React-owned only under `/app/*`.

This change applies the established pattern to `/dashboard` and `/projects`. Everything it needs on the backend already exists except two additive JSON fields:

- `Dashboard.jsx` and `GET /api/dashboard` exist and already derive from the same `_dashboard_context` as the Jinja route (`react_shell.py:194-196`), so the data cannot drift.
- `GET /api/projects` exists (`react_shell.py:618`) and returns active projects with capability and task counts.
- `POST /projects/{id}/archive`, `POST /projects/{id}/restore`, and `POST /settings/project/connect` already negotiate JSON outcomes for React callers (`portal.py:675-702`).

The net-new work is a React Projects view: `/projects` has no React equivalent today.

## Goals / Non-Goals

**Goals:**

- `/dashboard` and `/projects` select React when the complete build is available and the existing Jinja page when it is missing or partial.
- A React Projects view at parity with `projects.html`: open-local-repo, Local-Runner notice, capability pills, entry cards, Archive, archived list with Restore.
- The normal authenticated landing targets `/dashboard`, so Login (slice 10) can be written against its final URL once.
- React's estimation-accuracy panel stops diverging from the plan and the Jinja page at the moment it becomes the canonical dashboard.

**Non-Goals:**

- Canonical `/projects/{project_id}` and `/projects/{project_id}/board` (the following slice).
- `/board`, a redirect shim onto the first connected project's board (`portal.py:644-650`). It needs no React view in either slice.
- Making `/app` a redirect or deleting any Jinja template — the final retirement change does both, together.
- Unifying the error-handling tiers across all React views (see Decision 6).
- New mutations, schema, or changes to launch/estimation/budget/archive semantics.

## Decisions

### 1. Projects data comes from an extended `/api/projects`, not `/api/settings/project`

`GET /api/settings/project` already returns almost exactly what the Jinja `/projects` page renders: `local_runner_enabled`, connected projects with capability, archived projects, and the current error. Reusing it would need zero backend work.

Rejected. That endpoint is shaped for the Settings surface — it also carries Local Runner backend status and feeds the read-only-proof action. Binding the Projects entry page to it couples two surfaces that change for different reasons: a future Settings-only field becomes a Projects concern, and vice versa. The coupling would be by coincidence of current shape, not by domain.

Instead `/api/projects` — already the projects endpoint, already consumed by Board, Workspace, and Task History — gains `archived_projects` and `local_runner_enabled`. Both derive from the same `_archived_project_view_models` and settings flag the Jinja route uses, so no rule is duplicated and no second source of truth appears. The addition is additive: the existing `projects` array is untouched, so the three current consumers are unaffected.

### 2. Project entry cards link to `/app/projects/{id}` in this slice

`/projects/{id}` still renders Jinja until the following slice. A Projects card could link to the canonical `/projects/{id}` (correct final URL, but a full-page React→Jinja bounce out of the shell on every project open) or to `/app/projects/{id}` (React, in-shell, one link the following slice rewrites).

Chose `/app/projects/{id}`. It matches what the React dashboard's project cards already do, keeps the shell coherent, and the churn is a single link target. A full-page transition out of React on the primary navigation path is a worse regression than a one-line rewrite in the next slice.

### 3. `/app` keeps serving the shell; it does not become a redirect here

After this change, both `/app` and `/dashboard` render the React dashboard. That duplicate ownership is deliberate and bounded: `/app` is the transitional alias the spec always described, and the retirement change flips it to a permanent redirect once every canonical surface is React-owned. Making it a redirect now would strand `/app/projects/{id}` and `/app/projects/{id}/board`, which are still the only React-owned workspace and board URLs until the following slice.

### 4. The default landing moves to `/dashboard` now

`_default_portal_landing` (`portal.py:1934-1940`) returns `/app` when the build is available. Once `/dashboard` is build-aware React, `/app` is a redundant hop through an alias. Moving it now means Login (slice 10) targets its final URL once instead of hardcoding `/app` and being rewritten immediately.

The missing/partial-build landing is unchanged: first connected project, otherwise `/projects`. Note that `/projects` is itself build-aware after this change, so the fallback landing resolves to the Jinja projects page for exactly the build states that triggered the fallback. That is consistent, and the routing matrix test covers it.

### 5. React's estimation-accuracy panel is corrected in this slice

`db.estimation_accuracy` returns `completed_count: None` when no Done task has both an estimate and an actual — the fresh-install state every new operator sees. Jinja hides the whole panel (`dashboard.html:143`); React renders the section unconditionally and shows a "0 of 3 needed" progress state (`Dashboard.jsx:194`). The plan's dashboard requirement says "estimation accuracy when available", so Jinja matches the spec and React does not.

This slice is what makes React the canonical `/dashboard`, so it owns the drift rather than shipping a known spec violation to the front door. The fix is one conditional: render nothing when `completed_count` is null. The non-null-but-under-3 progress state is unchanged and already matches Jinja.

### 6. Error handling follows the existing per-view pattern

`Dashboard.jsx:18` renders `{error.message}` raw, which the plan forbids in operator-facing error UI. Its error branch is already being edited here to drop the "Open the server-rendered dashboard" escape link (Decision 7), so it adopts the established `safeError` treatment at the same time; the new Projects view does likewise.

`safeError` is deliberately a small per-view local, not a shared import: the four existing copies (`Setup.jsx:5`, `Sessions.jsx:6`, `SessionReport.jsx:6`, `Alarms.jsx:27`) each carry surface-specific copy ("Alarms require sign-in", "Setup state requires sign-in"). This slice follows that pattern rather than inventing a third one. Unifying all six — plus the remaining raw-`error.message` views in Budget, Control Plane, and Worker Settings — stays a separate follow-up, since those views are not otherwise touched here.

### 7. React→Jinja escape links go

`Dashboard.jsx:21` offers "Open the server-rendered dashboard". Once `/dashboard` is the React route, that link points at a fallback rather than a destination, and after retirement it points at nothing. It is removed. `Board.jsx:138` carries the equivalent board link and is left to the following slice, which owns that surface.

## Risks / Trade-offs

- **The fallback landing resolves through a now-build-aware `/projects`** → The missing-build landing redirects to `/projects`, which serves Jinja precisely when the build is missing. Correct by construction, but only because both decisions agree; an executable routing-matrix test over auth-required × built/missing/partial pins it.
- **`/app` and `/dashboard` both render the dashboard until retirement** → Bounded and specified as an alias, not an accident. The risk is that retirement forgets to flip `/app`; the retirement change already owns an invariant test that normal routes do not render retired templates.
- **Decision 2 knowingly writes a link the next slice rewrites** → One line, and the alternative degrades the primary navigation path for a whole slice.
- **Dashboard parity is asserted, not assumed** → `/api/dashboard` and Jinja share `_dashboard_context`, so data cannot drift, but the two renderers can still disagree (Decision 5 is exactly that). React's Connected-projects panel (`Dashboard.jsx:220-244`) has no Jinja equivalent and is a deliberate superset, not drift; it stays.
- **A vacuous test is the real hazard here** → Slice 9 shipped a tracking test that passed against the old template. The Decision 5 fix must be mutation-checked: the test has to fail against the current unconditional React panel, not merely pass against the fixed one.

## Migration Plan

No data migration. Deployment is the existing build-aware selection, so rollback is reverting the route changes; the Jinja pages remain in place and unmodified throughout this slice.

## Open Questions

None. The slice 10 vs 11 ordering and the accuracy-drift disposition were both settled before this change was drafted.
