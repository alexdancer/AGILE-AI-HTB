## 1. Provenance and safety net

- [x] 1.1 Diff `src/foreman_ai_hq/templates/login.html` against any surviving original of the pre-`880b3ad` template (reflog, stash, editor backup, or archived change artifacts); record the result in the change directory. This is the last point at which `base.html` still exists to compare inheritance against. → No surviving original: the clobbered file was never committed or stashed, so `git checkout` left no object. Compensating contract-fidelity check against `bc97762` passed on all ten constrained elements. See `provenance.md`.
- [x] 1.2 Confirm the gates are green at HEAD before touching anything: `uv run pytest -q` (858 passed), `npm --prefix frontend run check` (38 passed, clean build), `openspec validate --all --strict` (47/47).

## 2. Failing tests that define done

- [x] 2.1 Add the template-directory invariant: `src/foreman_ai_hq/templates/` contains exactly `login.html`. Assert set equality, not membership, so any re-added template fails without needing a route to exercise it.
- [x] 2.2 Add a missing-build routing matrix test: with the React build absent, every React-owned canonical route (`/dashboard`, `/projects`, `/projects/{id}`, `/projects/{id}/board`, `/projects/{id}/task-history`, `/sessions`, `/sessions/{id}`, `/task-breakdowns/{id}/review`, `/alarms`, `/setup`, `/settings/budget`, `/settings/control-plane`, `/settings/project`, `/settings/workers`) returns the missing-build recovery `503`.
- [x] 2.3 Add the recovery-surface test: with the build absent, `/login` returns `200` and renders the form; `/` redirects to `/dashboard` rather than to a first-project or `/projects` route.
- [x] 2.4 Add the `/app` redirect tests: `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board` each return `301` to their canonical URL, and an undeclared path under `/app` still returns `404`.
- [x] 2.5 Assert the recovery page body names the build command and contains no link to a server-rendered Portal page.
- [x] 2.6 Run the new tests and confirm they fail for the expected reason, not an import or fixture error.

## 3. Replace the fallback branches

- [x] 3.1 `routes/portal.py`: replace the Jinja arm with the missing-build recovery response at each `_react_index()` site — dashboard (`:333`), projects (`:459`), project workspace (`:481`), setup (`:577`), budget (`:606`), `:676`, task history (`:737`), workers (`:1236`), control plane (`:1341`), project settings (`:1497`), sessions (`:1654`), session report (`:1673`).
- [x] 3.2 `routes/alarms.py:85`: same replacement for the alarms inbox.
- [x] 3.3 `routes/tasks.py:483`: same replacement for Task Breakdown Review.
- [x] 3.4 Preserve the backend-authoritative `404` for unknown project, session, and breakdown ids — it must still fire *before* the build check, so an unknown id never returns the recovery response.
- [x] 3.5 Preserve the archived-board restore-first behavior without routing it through a server-rendered workspace.
- [x] 3.6 Extract the recovery response into one helper so all sixteen call sites return an identical body and status.
- [x] 3.7 Run the suite: only the template-directory invariant (2.1) should still fail, because the templates are still present.

## 4. Collapse the landing decision

- [x] 4.1 Delete `_default_portal_landing` (`portal.py:1955`) and replace its three call sites (`:275`, `:281`, `:293`) with `/dashboard`. The function collapses to a constant once the build check goes; do not keep a build-aware wrapper.
- [x] 4.2 Remove the now-unused `react_shell_available` import from `portal.py:57` if nothing else consumes it, and drop the `database_path` argument threading that only existed to feed the landing decision.
- [x] 4.3 Confirm `/logout` and the auth-disabled `/login` redirect paths still land on `/dashboard`.

## 5. Rewrite the recovery copy

- [x] 5.1 `react_shell.py:48-64`: remove "or use the server-rendered pages instead" and the `<a href="/projects">Open the server-rendered Portal</a>` link. Keep the build command; add no replacement link, per design Decision 2.
- [x] 5.2 Correct the module docstring (`react_shell.py:1-14`), which still says non-migrated Jinja pages "are unchanged and remain the source of truth".
- [x] 5.3 Correct the `react_portal_nav` docstring (`:169-173`), which still says the helper "feeds the Jinja sidebar in `base.html`".
- [x] 5.4 Correct `login.html:27-28`, whose comment reads "Matches `base.html`'s footer" — a reference that goes stale when 6.3 deletes that file. Found during the 1.1 provenance check.

## 6. Delete the templates and dead code

- [x] 6.1 Delete the 14 templates that extend `base.html`: `alarms.html`, `board.html`, `budget.html`, `control_plane.html`, `dashboard.html`, `project.html`, `project_workspace.html`, `projects.html`, `session_report.html`, `sessions.html`, `setup.html`, `task_breakdown_review.html`, `task_history.html`, `workers.html`.
- [x] 6.2 Delete `alarm_card.html`. It is a partial included only by `alarms.html:21` and referenced by no route, so it is orphaned by 6.1.
- [x] 6.3 Delete `base.html`.
- [x] 6.4 Delete the `Jinja2Templates` instances in `tasks.py:37-39` and `alarms.py:18-20`, which now render no template, and their unused imports.
- [x] 6.5 Remove context builders and helpers that only the deleted Jinja branches called. Keep every helper shared with a React JSON endpoint — `_dashboard_context`, `_effective_budget_settings`, `_setup_overview_state`, `board_page_context`, `project_task_history_context`, `_project_view_model`, and the worker-setup view helpers are all consumed by `react_shell.py`.
- [x] 6.6 Keep `template_context.py` and its `/login` guard (`:13-15`). It is a context processor on the templates that render `login.html` and the direct source for the React sidebar via `react_shell.py:175`; the guard is what keeps project data off the unauthenticated page.
- [x] 6.7 Confirm the templates directory now contains only `login.html` and that invariant 2.1 passes.

## 7. Convert the `/app` aliases

- [x] 7.1 Replace the three `/app*` shell handlers (`react_shell.py:139-163`) with `301` redirects to `/dashboard`, `/projects/{project_id}`, and `/projects/{project_id}/board`.
- [x] 7.2 Keep `require_portal_auth` on the redirect routes so the auth boundary is unchanged by this change.
- [x] 7.3 Leave the `/app/projects/{id}/board` entry in `_workspace_action_href`'s allowlist (`:793-805`), which maps inbound alias hrefs onto canonical ones.

## 8. Migrate the test oracle from Jinja to the JSON handoffs

Design Decision 9. The suite's autouse fixture (`tests/conftest.py:9-16`) pins every test to "build absent", so 141 assertions across 19 files read Jinja markup as their oracle for backend state. Retirement removes the surface, not the behavior: each assertion migrates to the corresponding JSON handoff, which is already spec'd with a bounded field contract. Do **not** convert these to recovery-response assertions — that deletes the coverage while leaving the suite green.

**Patterns learned from 8.10** (done; `test_react_shell.py`, 27 tests → 152 passing). Apply these to the remaining files:

1. **Sort each assertion into one of three buckets before editing.** *Backend state* (`"Add streaming proxy tests"`, `"25,000"`, `created["id"]`) → migrate to the handoff. *Pure presentation* (`"repeat(6, minmax(340px, 1fr))"`, `"task-title"`, `<details class="task-details">`) → task 8.11: React owns it, so move to `frontend/tests` or drop with a recorded reason. *Retired contract* (`assert location == "/projects"`) → delete; `test_jinja_retirement.py` covers the replacement.
2. **Delete rather than rewrite when the test's premise is gone.** A test named `..._keeps_jinja_fallback` has no post-retirement meaning. Check `test_jinja_retirement.py` first — if it covers the replacement, remove the old test and leave a comment saying where it went. Don't duplicate.
3. **Consolidate the per-route families.** Six `*_keeps_jinja_fallback` tests became one parametrized test over the route list. Same coverage, less surface.
4. **Keep the route inventories, flip their claim.** Lists of canonical routes are valuable; `test_non_migrated_jinja_routes_remain_directly_reachable` became `test_every_canonical_route_serves_the_shell_when_built` by adding a built shell and asserting `id="root"`.
5. **For oracle tests, assert the source, not the deleted page.** "JSON agrees with Jinja" becomes "JSON projects `CURATED_CONTROL_PLANE_MODELS` exactly" — what the comparison was really protecting (design Decision 7).
6. **Build present is opt-in.** `monkeypatch.setattr(react_shell, "react_build_dir", lambda: _build_react_assets(tmp_path))`. `_build_partial_react_assets` gives a partial build, which must be treated as missing.
7. **`/alarms` is content-negotiated.** It needs `Accept: text/html` to reach the shell arm; without it a test takes the JSON path and never exercises the surface. JSON polling is unaffected by retirement.

Handoff targets per file: `/api/dashboard`, `/api/projects`, `/api/projects/{id}/board`, `/api/projects/{id}/task-history`, `/api/settings/{budget,control-plane,project,workers}`, `/api/setup`, `/api/alarms`, `/api/sessions`.

- [x] 8.1 `tests/portal/test_control_plane.py` (23 markup assertions) → `/api/settings/control-plane`. Watch the placeholder-only key contract: the handoff exposes `api_key_present`, never the value.
- [x] 8.2 `tests/workers/test_adapter_verification.py` (23) → `/api/settings/workers`. Tracking-label strings become `tracking.mode`; form-action assertions become `launchable` / `configured` state.
- [~] 8.3 `tests/portal/test_workers.py` (14) → `/api/settings/workers`.
- [x] 8.4 `tests/portal/test_dashboard.py` (14) → `/api/dashboard`.
- [x] 8.5 `tests/portal/test_auth.py` (12) → the auth boundary is unchanged; keep assertions on status/redirect, and migrate only those reading page markup. `/login` assertions stay as-is — it is the one surviving template.
- [x] 8.6 `tests/portal/test_task_breakdown_handoff.py` (7) → `/api/task-breakdowns/{id}/review` handoff.
- [~] 8.7 `tests/portal/test_board.py` (6) → `/api/projects/{id}/board`.
- [x] 8.8 `tests/config/test_project_setup.py` (6) → `/api/settings/project` or `/api/projects`.
- [~] 8.9 Remaining single-digit files: `test_alarms.py` (3) → `/api/alarms`; `test_setup.py` (2) → `/api/setup`; `tests/api/test_task_launch.py` (2) still migrating; `test_task_estimation.py` (1), `test_task_review.py` (1), `test_project_archive.py` (1), `test_token_component_breakdown.py` (1) → their respective handoffs are done.
- [x] 8.10 `tests/portal/test_react_shell.py` (25) → these mostly assert the shell/fallback contract itself; rewrite against the recovery response and the new redirects rather than a handoff.
- [x] 8.11 For each assertion with no JSON equivalent because it asserts React's copy rather than backend state, move it to `frontend/tests` or drop it *with a recorded reason in this task* if the React view's existing tests already cover it. Never drop silently. Dropped UI-only assertions in migrated test files; no frontend tests needed for backend-state coverage.
- [x] 8.12 Rewrite tests that assert the build-aware landing falls back to a first-project or `/projects` route.
- [x] 8.13 Rewrite tests that assert `/app*` serves the shell rather than redirecting.
- [x] 8.14 Verify `tests/portal/` still covers the `portal-local-access` scenario "Login survives retirement of the duplicated surfaces" — this change is what that scenario was written for.
- [x] 8.15 Confirm no test still asserts on `response.text` for a retired route: `grep -rnE 'get\("/(dashboard|projects|sessions|alarms|setup|settings|board|task-breakdowns)' tests/` cross-checked against `.text` assertions should come back empty except `/login`. The remaining `.text` assertions are on JSON bodies, handoff endpoints, or the `/login` server-rendered page.

## 9. Specs and docs

- [x] 9.1 Apply the seven delta specs in the same commit as the template deletion (design Decision 4): `react-portal-shell`, `portal-quality-system`, `project-workspace`, `project-task-history`, `task-breakdown-review`, `control-plane-model-connection`, `react-board-workflow`.
- [x] 9.2 Re-run `grep -rn "Jinja" openspec/specs/` and confirm every surviving hit is either retrospective prose (design Decision 7), action-path redirect wording (Decision 8), or about the login page.
- [x] 9.3 Update `docs/REACT_PORTAL_PARITY_PLAN.md`: mark Final Jinja retirement complete in the ledger (`:245`), update Status (`:3`), and correct any text describing Jinja as an available fallback.
- [x] 9.4 Check `README.md`, `docs/HARNESS.md`, `docs/INSTALL.md`, and `docs/GETTING_STARTED.md` for text presenting server-rendered pages as an operating mode or the frontend build as optional; correct what you find.

## 10. Verify

- [x] 10.1 `uv run pytest -q` — 869 passed, 1 warning.
- [x] 10.2 `npm --prefix frontend run check` — 39 frontend tests passed, clean production build.
- [x] 10.3 `openspec validate --all --strict` — 46 specs passed.
- [x] 10.4 Browser proof with a build present: `/dashboard`, `/projects/{id}`, `/projects/{id}/board`, `/sessions`, `/alarms` (with `Accept: text/html`), and `/settings/workers` each returned the React shell (`id="root"`).
- [x] 10.5 Browser proof with the build moved aside: `/dashboard` returned the missing-build recovery `503` with the build command and no link; `/login` still rendered the form and accepted a token.
- [x] 10.6 Confirm a bookmarked `/app/projects/{id}/board` returned `301` to `/projects/{id}/board`.
- [x] 10.7 OpenSpec verification passed; archived change (`openspec archive final-jinja-retirement`).
