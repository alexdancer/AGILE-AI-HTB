# React Portal Parity Migration Plan

> **For Hermes:** Use this as the reference plan before starting the next OpenSpec change. Do not make React the default authenticated Portal until the parity gates below pass.

**Goal:** Move AGILE-AI-HTB toward a coherent React authenticated operator console without leaving operators in a partial `/app` island that lacks the real Portal layout, dashboard, and AGILE Board behavior.

**Architecture:** FastAPI remains authoritative for authentication, persistence, task estimation, launch guardrails, Worker Run execution, token budget governance, review disposition, and audit evidence. React may own the authenticated operator console UI once it preserves the existing Portal chrome and reaches functional parity for each migrated surface. Jinja stays as login/missing-build/error fallback and can remain the implementation for surfaces that are not yet parity-migrated.

**Current problem:** The current React shell under `/app` is a bridge surface, not the full app. It has a different layout from the Jinja Portal, no dashboard-equivalent home, and an incomplete AGILE Board that punts back to the server-rendered board for launch/review behavior. Making that surface the default landing creates a split-brain product experience.

---

## Product Direction

Commit to React for the main authenticated operator console **eventually**, but do not keep a separate-feeling `/app` mini-application as the default.

Target end state:

```text
/ or authenticated landing
└─ React Portal shell
   ├─ Dashboard
   ├─ Projects
   ├─ Project workspace
   ├─ AGILE Board
   ├─ Sessions
   ├─ Alarms
   ├─ Setup
   └─ Settings

FastAPI owns all backend rules and workflow state.
Jinja remains fallback/non-migrated support until replaced surface-by-surface.
```

Non-goals:

- Do not duplicate backend guardrail, estimation, launch, review, budget, or evidence rules in React.
- Do not keep `/app` as a separate product with different navigation/chrome.
- Do not make React default before dashboard and board parity are proven.
- Do not big-bang rewrite every Jinja route at once.

---

## Phase 1: Roll Back the Incomplete React Default

**Objective:** Restore the full existing Portal as the authenticated landing while React parity work continues.

**Behavior:**

- Root `/` and successful login should land on the existing full Portal surface, likely `/dashboard` or `/projects`.
- `/app` remains available as an experimental/migrated route.
- Missing React build behavior remains safe: no blank shell, clear fallback/error.

**Likely files:**

- Modify: `src/agile_ai_htb/routes/portal.py`
- Modify: `src/agile_ai_htb/routes/react_shell.py` if build-aware helper behavior needs adjustment
- Test: `tests/portal/test_react_shell.py`

**Verification:**

```bash
openspec validate <change-name> --strict
npm --prefix frontend run check
uv run pytest tests/portal/test_react_shell.py -q
uv run pytest -q
git diff --check
```

**Acceptance criteria:**

- Authenticated root/login do not land users in incomplete `/app` by default.
- `/app` still works when built.
- Missing/partial React build still never renders a broken blank shell.

---

## Phase 2: React Uses the Real Portal Chrome

**Objective:** Make the React shell feel like the same app before adding more React surfaces.

React shell must preserve the Jinja layout contract from `src/agile_ai_htb/templates/base.html`:

- top brand
- sidebar
- project list
- active project context
- `+ Open local repo`
- Setup group
- Governance group
- Settings group
- logout when auth is enabled
- footer
- active navigation state
- same color/theme tokens and shared primitives

**Likely files:**

- Modify/create: `frontend/src/components/Shell.jsx`
- Modify/create: React sidebar/nav components under `frontend/src/components/`
- Modify: `frontend/src/tokens.css`
- Modify: backend JSON endpoint(s) if React needs sidebar project data
- Test: `tests/portal/test_react_shell.py`
- Test: frontend build via `npm --prefix frontend run check`

**Implementation rule:**

React navigation may use client-side routing for React-owned paths, but links to non-migrated Jinja surfaces should remain normal full-page anchors until those surfaces are migrated.

**Acceptance criteria:**

- React and Jinja share the same visual app frame.
- Sidebar project entries are available in React.
- Non-migrated pages remain reachable from React chrome.
- Active route/project state is clear.

---

## Phase 3: React Dashboard Parity

**Objective:** `/app` should become a real dashboard-equivalent front door, not only a project picker.

React dashboard should include the same operator intent as `src/agile_ai_htb/templates/dashboard.html`:

- Operator next actions
- Daily governed budget KPI
- Worker execution token KPI
- open/critical alarm KPI
- budget spend breakdown
- active sessions preview
- recent alarms preview
- estimation accuracy when available
- project entry points

**Likely files:**

- Create/modify: `frontend/src/views/Dashboard.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `src/agile_ai_htb/routes/react_shell.py` or route module for dashboard JSON
- Reuse existing dashboard helper logic where available; do not duplicate domain rules in React
- Test: JSON endpoint auth and shape
- Test: source/contract assertions for React field names

**Acceptance criteria:**

- `/app` answers “what should the operator do next?”
- Dashboard data comes from authenticated FastAPI JSON.
- Dashboard links route to existing workflows without duplicating backend actions.
- React dashboard does not regress the existing Jinja dashboard until replacement is complete.

---

## Phase 4: React AGILE Board Functional Parity

**Objective:** React board must not replace the Jinja board until it supports the real operator workflow.

Parity with `src/agile_ai_htb/templates/board.html` must include:

- board status toolbar
- project-scoped counts and history link
- Run automation panel
- `Run next task`
- `Run queue` / `Stop queue`
- `auto_agent_review` option
- task intake form
- Markdown upload
- task filtering
- columns: Estimated, Running, Review, Done, Blocked
- compact card summary
- estimate/model/actual token display
- Worker Adapter selector
- Worker model selector constrained by adapter allowed models
- budget override controls
- native-usage budget acknowledgement when required
- Launch task action
- refresh running task action
- review prompt save
- Agent Review action
- Mark Done action
- Block action with reason
- Archive/Archive all Done/Dismiss actions
- launch diagnostics
- token component details
- task details/raw evidence
- session/report links
- empty states and guardrail-blocked setup links

**Likely files:**

- Modify: `frontend/src/views/Board.jsx`
- Create: board subcomponents under `frontend/src/components/` or `frontend/src/views/board/`
- Modify: `frontend/src/tokens.css`
- Modify/add authenticated JSON endpoints for board state if existing state is insufficient
- Prefer existing POST form endpoints for actions until a JSON mutation API is explicitly specified
- Test: `tests/portal/test_react_shell.py`
- Consider additional frontend source contract tests for required field names/actions

**Implementation rule:**

If a feature cannot be ported safely yet, the React board should clearly link to the Jinja board and must not be promoted as the replacement/default board.

**Acceptance criteria:**

- Operators can perform the normal board loop in React: intake → estimate → launch → running refresh/status → review → done/block/archive.
- React uses backend-authoritative routes/data for every workflow decision.
- Jinja board and React board agree on task state, launch readiness, and evidence display.
- Tests cover every launch/review/action form that matters.

---

## Phase 5: Migrate Remaining Operator Surfaces Deliberately

**Objective:** Move the rest of the authenticated Portal into React only after the main loop is coherent.

Candidate order:

1. Projects list and project workspace
2. Sessions list/report previews
3. Alarms inbox
4. Setup overview
5. Worker settings
6. Control-plane settings
7. Budget settings
8. Project settings

For each surface:

- Read the Jinja template and route helper first.
- Add authenticated JSON endpoint only if needed.
- Keep FastAPI authoritative for mutations.
- Add regression tests for auth, JSON shape, and action behavior.
- Do not remove the Jinja path until React parity is verified or fallback is explicitly retained.

---

## Phase 6: Make React the Default Again

**Objective:** Re-enable React as the authenticated landing only after parity gates pass.

Default landing can return to React when:

- React shell uses full Portal chrome.
- React dashboard is dashboard-equivalent.
- React AGILE Board is functionally equivalent for the normal governed task lifecycle.
- Missing/partial build fallback is safe.
- Non-migrated fallback links are explicit and not confusing.
- Tests prove root/login routing behavior under auth-required and auth-disabled modes.

**Verification gate:**

```bash
openspec validate <change-name> --strict
npm --prefix frontend run check
uv run pytest tests/portal/test_react_shell.py -q
uv run pytest -q
git diff --check
```

Add browser/manual smoke evidence before declaring the UI replacement complete:

1. Open root after build.
2. Confirm dashboard appears in full Portal chrome.
3. Open project workspace.
4. Open project board.
5. Confirm task intake, filtering, launch/review controls, and details are present.
6. Confirm non-migrated pages still reachable.
7. Confirm missing-build fallback still works.

---

## Proposed OpenSpec Changes

Recommended sequence:

1. `react-portal-default-rollback`
   - Restore stable default landing while React is incomplete.

2. `react-portal-shell-chrome-parity`
   - Port full app chrome/sidebar/project nav into React.

3. `react-dashboard-parity`
   - Make `/app` a dashboard-equivalent home.

4. `react-board-functional-parity`
   - Port the AGILE Board workflow fully enough to replace Jinja board.

5. `react-portal-default-enable`
   - Make React default only after parity tests pass.

Each change should be small enough to verify independently.

---

## Testing Strategy

Use tests to prevent another premature default switch:

- Root/login routing tests:
  - auth disabled
  - auth required without cookie
  - auth required with valid signed cookie
  - built React assets
  - missing React assets
  - partial React build

- React source/contract tests:
  - no stale field names such as `estimated_tokens` for task estimate display
  - board card uses `description`
  - queue start includes `auto_agent_review`
  - required form actions are present before React board can be default

- Backend JSON tests:
  - endpoints require portal auth
  - endpoint shapes match React callers
  - project and board data reuse existing helpers/domain behavior

- Build/tests:

```bash
npm --prefix frontend run check
uv run pytest tests/portal/test_react_shell.py -q
uv run pytest -q
git diff --check
```

---

## Decision Log

- React is the right long-term direction for the authenticated operator console because AGILE-AI-HTB is becoming an interactive control plane: dashboard next actions, project switching, board controls, setup workflows, queue state, review controls, evidence panels, and future live updates are app-like interactions.
- React should not be an incomplete separate `/app` island.
- Backend authority remains in FastAPI. React is a presentation/client-state layer, not a duplicate workflow engine.
- The existing Jinja Portal remains the reliable fallback until each React surface reaches parity.
