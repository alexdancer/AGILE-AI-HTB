## Why

Every Portal surface now renders React on its canonical URL. The Jinja templates that fed those same URLs survive only as missing-build fallback and parity oracle — a second implementation of thirteen surfaces, kept alive to answer a case that a single recovery page answers better. Phase 5 closed the last precondition (slice 11b took the canonical URLs; slice 10 made login standalone), so the duplication now has no remaining job.

Retiring it is the final slice of the React Portal parity migration. Until it lands, every future Portal change pays a two-implementation tax, and the specs continue to promise a fallback the operator should never reach.

## What Changes

- **BREAKING** Delete `base.html`, the 14 templates that extend it, and the `alarm_card.html` partial they include. `login.html` remains as the standalone Portal Recovery Surface.
- **BREAKING** Every React-owned canonical route stops falling back to Jinja when the build is missing or partial, and returns the missing-build recovery response instead. This inverts today's contract, which promises the operator a working server-rendered page at the same URL.
- **BREAKING** The default authenticated landing stops being build-aware. `/`, successful login, and auth-disabled login redirect to `/dashboard` unconditionally; a missing build surfaces as the recovery response there rather than diverting to a first-project or `/projects` Jinja landing.
- Rewrite the missing-build recovery copy. It currently offers "use the server-rendered pages instead" and links to `/projects` — after retirement that advice is wrong and the link returns the same error. Recovery becomes: build the frontend.
- `/app`, `/app/projects/{project_id}`, and `/app/projects/{project_id}/board` become permanent redirects to their canonical URLs, ending their transitional-alias status.
- Add an invariant test that normal routes cannot render a retired template, so re-introduction fails a test rather than being discovered later.

Explicit non-goals: no change to authentication strength, workflow rules, JSON handoff contracts, or the React views themselves. The action endpoints that React calls are shared, not duplicated, and are untouched.

## Capabilities

### New Capabilities

None. This change removes an implementation; it introduces no new operator-facing capability.

### Modified Capabilities

- `react-portal-shell`: The shell's central promise inverts. "React is the build-aware default authenticated landing" and every "missing or partial build keeps X in Jinja" scenario describe a fallback that no longer exists; the missing-build response becomes the single answer for all React-owned routes, and `/app/*` aliases become redirects.
- `portal-quality-system`: "Portal remains server-rendered" and its two scenarios — "No frontend framework is required for Jinja fallback and non-migrated pages" and "Non-migrated pages require no frontend build step" — are true today and false after this diff. They must change in this same change, not before it.
- `project-workspace`: "The Jinja overview SHALL remain available as fallback" goes false, along with the server-rendered project overview scenario.
- `project-task-history`: "the Jinja history page SHALL remain the missing/partial-build fallback and parity oracle" goes false.
- `task-breakdown-review`: The scenario "Missing or partial build preserves Jinja review" goes false.
- `control-plane-model-connection`: Its consistency requirement spans "the Jinja control-plane page, the authenticated JSON read, and the React view". One of the three ceases to exist.
- `react-board-workflow`: The scenario "Existing Jinja form behavior remains available" becomes unreachable once `board.html` is deleted — no Jinja board form can submit. The negotiation requirement itself survives for non-JSON callers.

`portal-local-access` is deliberately **not** modified. Its scenario "Login survives retirement of the duplicated surfaces" (`spec.md:61`) already specifies this change's acceptance condition; retirement must satisfy it unchanged.

## Impact

Templates deleted (16): `base.html`, `alarm_card.html`, and `alarms.html`, `board.html`, `budget.html`, `control_plane.html`, `dashboard.html`, `project.html`, `project_workspace.html`, `projects.html`, `session_report.html`, `sessions.html`, `setup.html`, `task_breakdown_review.html`, `task_history.html`, `workers.html`. Retained: `login.html`.

Routes: roughly 15 fallback branches lose their Jinja arm and gain the recovery response — `routes/portal.py` (`:333`, `:459`, `:481`, `:577`, `:606`, `:676`, `:737`, `:1236`, `:1341`, `:1497`, `:1654`, `:1673`, and the landing decision at `:1954`), `routes/alarms.py:85`, and `routes/tasks.py:483`. `routes/react_shell.py` loses `_MISSING_BUILD_HTML`'s dead fallback link and gains the three `/app/*` redirects.

Dead code to remove with the templates: the Jinja-only context builders those branches call; `_default_portal_landing` (`portal.py:1955`), which collapses to a constant `/dashboard` once the build check goes and takes its `database_path` argument with it; and the `Jinja2Templates` instances in `tasks.py:37-39` and `alarms.py:18-20`, which render no template after retirement.

Deliberately retained: `template_context.py`'s `portal_template_context` and its `/login` guard (`:13-15`). It is registered as a context processor on the templates that render `login.html`, and it is also the direct source for the React sidebar via `react_shell.py:175`. The guard stops the one surviving template from querying project data before authentication, so retirement makes it more load-bearing, not less.

Stale comments to correct: `react_shell.py`'s module docstring and `react_portal_nav`'s docstring, which still describe serving "non-migrated Jinja pages" and feeding "the Jinja sidebar in `base.html`".

Tests: the largest single piece of work, and larger than it looks. `tests/conftest.py:9-16` pins every test to "build absent" through an autouse fixture, so the 858-test suite reaches Portal routes through the Jinja fallback by default. Roughly **141 assertions across 19 files in five test packages** (`tests/portal`, `tests/api`, `tests/workers`, `tests/config`, `tests/evals`) read rendered Jinja markup as their oracle for backend state — including suites that are not about the Portal at all, such as `tests/workers/test_adapter_verification.py`. Retirement removes the surface they read, not the behavior they check, so each migrates to the corresponding authenticated JSON handoff rather than to a recovery-response assertion. See design Decision 9.

Docs: `docs/REACT_PORTAL_PARITY_PLAN.md` ledger and Status; `README.md` / `docs/HARNESS.md` if either documents server-rendered pages as an operating mode.
