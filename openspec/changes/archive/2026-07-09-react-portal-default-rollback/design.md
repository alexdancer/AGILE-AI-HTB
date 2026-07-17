## Context

The archived change `2026-07-09-react-portal-front-door` made the React `/app` shell the default authenticated landing whenever the frontend was built. That landed as a single branch in `portal._default_portal_landing`:

```python
def _default_portal_landing(database_path):
    if _react_shell.react_build_available():      # ← premature default
        return "/app"
    projects = db.list_connected_projects(database_path)
    if projects:
        return f"/projects/{projects[0]['id']}"
    return "/projects"
```

`react_build_available()` has exactly one caller: that branch. The React shell at `/app` is a thin surface — it lacks the real Portal chrome, has no dashboard-equivalent home, and its AGILE Board punts back to the Jinja board for launch/review. Sending every authenticated operator there on every login creates a split-brain product experience.

The durable plan in `docs/REACT_PORTAL_PARITY_PLAN.md` sequences the fix: Phase 1 rolls back the default, Phases 2–5 build real parity (chrome, dashboard, board), Phase 6 re-enables React as default. This design covers Phase 1 only.

Routing today:

```
                     BEFORE (premature)              AFTER (Phase 1)
                     ─────────────────────           ──────────────────────────
 GET /  (auth off)   → /app  if built                → /projects (or /projects/{first})
                     → /projects if no build         → /projects (same)
 POST /login (ok)    → /app  if built                → /projects (or /projects/{first})
                     → /projects if no build         → /projects (same)
 POST /logout (off)  → /app  if built                → /projects (or /projects/{first})
                     → /projects if no build         → /projects (same)
 GET /app  (built)   → React shell 200               → React shell 200 (UNCHANGED)
 GET /app  (no build)→ 503 missing-build page         → 503 missing-build page (UNCHANGED)
```

## Goals / Non-Goals

**Goals:**
- Authenticated root, login success, and auth-disabled logout no longer land on `/app` regardless of whether the React build is present.
- The `/app` route, its JSON endpoints, build detection, and missing/partial build fallback stay unchanged and reachable.
- Tests prove the rollback under: built assets, missing assets, partial assets, auth disabled, auth required with no cookie, auth required with valid signed cookie.

**Non-Goals:**
- No React frontend code change. `frontend/` is untouched.
- No new UI link to `/app`. Discoverability of `/app` during the interim is a Phase 2 chrome concern.
- No "experimental" badge or labelling on `/app` — that is a chrome change, not a routing rollback.
- No removal or rename of `/app`, `/api/projects`, `/api/projects/{id}/workspace`, or `/api/projects/{id}/board`.
- No new config flag or setting to toggle the default. A toggle risks re-creating the bug. Phase 6 reintroduces a real gated helper alongside parity tests; this change does not pre-wire it.
- No dashboard, chrome, sidebar, or board parity work — those are Phases 2–4.

## Decisions

### Decision 1: Delete `react_build_available()` and the `/app`-first branch (Option A)

Remove the `if _react_shell.react_build_available(): return "/app"` branch from `_default_portal_landing` and delete the `react_build_available()` function from `react_shell.py`.

**Rationale:** The helper has exactly one caller — the premature default. Keeping it around as dead code (Option B) leaves a latent re-enable trap and contradicts the rollback's intent. A future Phase 6 can reintroduce a helper *and* its gate together, at which point the gate is real (parity tests pass). The `/app` route, `_react_index()`, `_referenced_assets_available()`, the 503 missing-build response, and all JSON endpoints stay — only the landing-preferring helper goes.

**Alternatives considered:**
- *Option B — keep `react_build_available()`, ignore it in the landing.* Rejected: dead code, lint risk, and reintroduces a half-state the plan warns against.
- *Option C — add a settings flag (e.g. `react_default_landing`).* Rejected: a toggle for a temporary state risks operators re-enabling the bug, and the plan explicitly says React should not be default until parity gates pass.

### Decision 2: `/app` stays silently reachable, no added link

The `/app` URL continues to serve the React shell when built (and the 503 page when not). No dashboard, projects, or sidebar link to `/app` is added in this change.

**Rationale:** Adding a "Try experimental console" link mixes a chrome change into a routing rollback and re-introduces a second-app entry point — the exact split the rollback removes. Operators who need `/app` during the interim can type the URL. Link surfacing belongs to Phase 2 where React chrome is defined.

### Decision 3: Three existing tests flip; one new regression test added

- `test_landing_prefers_react_shell_when_built` → flip assertion from `/app` to the Jinja landing (`/projects` with no projects, `/projects/{first}` with projects).
- `test_authenticated_root_prefers_react_shell_when_built` → same flip.
- `test_login_redirects_to_react_shell_when_built` → same flip.
- New: a test that builds assets AND carries a valid signed cookie AND asserts the landing is the Jinja Portal, not `/app` — locks the rollback against a future regression that re-introduces the `/app`-first branch.

Existing tests that already match the rollback behaviour (`test_landing_falls_back_to_jinja_when_build_missing`, `test_authenticated_root_falls_back_to_jinja_when_build_missing`, `test_login_falls_back_to_jinja_when_build_missing`, `test_partial_react_build_falls_back_without_blank_shell`, `test_react_shell_served_when_built`, `test_react_shell_reports_missing_build`) stay green unchanged.

## Risks / Trade-offs

- **[Risk] An operator who relied on `/app` as the landing now lands on Jinja.** → Mitigation: expected and intentional; documented as **BREAKING** in the proposal. `/app` remains reachable at the same URL; only the default redirect changes. Phase 6 restores React as default with parity.
- **[Risk] Deleting `react_build_available()` loses a helper Phase 6 might want.** → Mitigation: the helper is ~3 lines; re-adding it alongside a real gate is cheaper than maintaining dead code through Phases 2–5. The decision is reversible and recorded here.
- **[Risk] A future change re-introduces the `/app`-first default without parity.** → Mitigation: the new regression test (built + valid cookie → Jinja) fails loudly if the branch returns. Phase 6 must update that test as part of re-enabling, forcing the author to confront the parity gate.
- **[Trade-off] `/app` becomes undiscoverable from the default UI during the interim.** → Accepted: this is the point of the rollback. Discoverability is deliberately deferred to Phase 2 chrome parity.