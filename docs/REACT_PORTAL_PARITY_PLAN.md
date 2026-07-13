# React Portal Parity Migration Plan

> **Status:** Portal chrome, Dashboard, project workspace, AGILE Board, Sessions/Session Report, Task Breakdown Review, and the React default-enable gate are complete. Remaining operator surfaces continue as full-page Jinja routes until migrated deliberately.

**Goal:** Move AGILE-AI-HTB toward a coherent React authenticated operator console without leaving operators in a partial `/app` island that lacks the real Portal layout, dashboard, and AGILE Board behavior.

**Architecture:** FastAPI remains authoritative for authentication, persistence, task estimation, launch guardrails, Worker Run execution, token budget governance, review disposition, and audit evidence. React owns every normal user-facing route after each surface reaches parity. During migration, Jinja may continue implementing non-migrated surfaces. In the final state, only a minimal server-rendered Portal Recovery Surface remains for login and recovery when the React build is missing or partial; it is not a second operator console.

**Current state:** A complete React build owns the authenticated front door, Dashboard, project workspace, normal governed AGILE Board loop, Sessions/Session Report, and canonical Task Breakdown Review. FastAPI selects the existing Jinja page when the React index or any referenced asset is missing. Alarms, Setup, Settings, and project task history remain ordinary full-page Jinja routes. Project task history is the next bounded parity candidate.

---

## Product Direction

React owns the main authenticated operator-console front door without becoming a separate-feeling `/app` mini-application. Remaining surfaces migrate only after bounded parity work.

Normal login also becomes React-owned. Minimal server rendering remains only as the Portal Recovery Surface when the React build cannot load.

Migrated React surfaces take over the existing canonical user-facing URLs (`/sessions`, `/alarms`, `/setup`, `/settings/*`, and equivalent project routes). Do not create a parallel `/app/*` route tree for remaining surfaces. During migration, each canonical GET may select React when the build is complete and its existing Jinja page when React is unavailable. Existing FastAPI mutation routes remain authoritative. `/app` is a transitional alias, not the final URL namespace.

After final migration, `/app`, `/app/projects/{project_id}`, and `/app/projects/{project_id}/board` stop rendering the frontend and remain only as permanent redirects to `/dashboard`, `/projects/{project_id}`, and `/projects/{project_id}/board`. This preserves old bookmarks without preserving duplicate route ownership.

Target end state:

```text
/ or authenticated landing
└─ React Portal shell
   ├─ Login
   ├─ Dashboard
   ├─ Projects
   ├─ Project workspace
   ├─ AGILE Board
   ├─ Sessions
   ├─ Alarms
   ├─ Setup
   └─ Settings

FastAPI owns all backend rules and workflow state.
Jinja remains non-migrated support until replaced surface-by-surface.
Minimal server-rendered login/recovery remains only when React cannot load.
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

0. Correct current Setup readiness so `Ready to launch` requires a launch-ready Connected Project
1. ✅ Sessions list and full Session Report as one read-only vertical slice
2. ✅ Task Breakdown Review
3. **Next:** Project task history
4. Alarms inbox
5. Budget settings
6. Control-plane settings
7. Worker settings
8. Project settings
9. Setup overview after all four destination Settings surfaces are React
10. Login and Portal Recovery Surface

For each surface:

- Read the Jinja template and route helper first.
- Add authenticated JSON endpoint only if needed.
- Extend React routing to the existing canonical user-facing URL; do not add a parallel `/app/*` URL for the migrated surface.
- Keep build-aware Jinja fallback on that canonical GET until the final retirement change.
- Keep FastAPI authoritative for mutations.
- Add regression tests for auth, JSON shape, and action behavior.
- Do not remove the Jinja path until React parity is verified or fallback is explicitly retained.

First remaining change: migrate `/sessions` and `/sessions/{session_id}` together. The list and report form one operator evidence workflow; splitting them would preserve an immediate React-to-Jinja transition and leave Alarms and Task Breakdown links dependent on an unmigrated report. This slice should add no new workflow mutations.

Session Report parity means information parity, not pixel parity. React must preserve the current summary plus every audit-detail path: token totals and categories, Worker token components, raw provider usage, budget-zone timeline, Worker Run timeline, Repo Context Brief, Alarms, Checkpoint results, and related Agent Review evidence. Dense/raw evidence may remain collapsed by default, but operators must not need the old Jinja report to inspect it.

The React `/sessions` list auto-refreshes while any session is active so running rows progress without a full-page reload. Polling stops when no active sessions remain. This does not establish a general real-time Portal contract.

An active React Session Report polls only lightweight freshness metadata. New token or event evidence shows a `New session evidence available` notice and explicit Refresh action; the full report never rewrites itself while the operator is reading. Freshness checks stop when the session reaches a terminal state. Refreshing may replace the report only after the operator chooses it.

The React Alarms inbox must not copy the current Dismiss-only limitation or expose arbitrary mutation payloads. It shows validated actions relevant to Alarm type and Session state: Continue where safe, Abort Session only for an active Session with confirmation, and typed positive-cap Raise Budget controls for budget Alarms with confirmation. Generic `adjust_guardrail` payload editing remains outside the Alarm inbox and should route operators to Guardrail configuration until a typed product contract exists. React Alarm data and actions require Portal authentication even though the existing general JSON Alarm route has a different auth boundary.

React Alarms provides bookmarkable Open, Resolved, and All filters, defaulting to Open. Resolved entries retain action, sanitized payload summary, resolution timestamp, and Session Report link so the existing `Audit kept` claim is visible rather than hidden in backend data.

Settings migrate before Setup Overview. Budget Settings establishes the simplest authenticated React mutation pattern, followed by Control Plane, Worker, and Project Settings. Setup migrates after those destinations so its next-action flow no longer sends operators back into Jinja. Do not combine all setup/settings work into one large change.

Setup Overview may show `Ready to launch` only when Control Plane, Token Budget, and Worker Adapter requirements pass and at least one Connected Project has `launch_ready` capability. The current Jinja implementation incorrectly treats Projects as optional and must be corrected before or with the relevant approved change; React must not copy that drift.

Before remaining React slices begin, use a small standalone OpenSpec change to correct that current Jinja Setup readiness claim and add targeted tests. Do not fold the truthfulness fix into Sessions or wait until the later React Setup migration.

Board-linked surfaces take priority over admin surfaces. Task Breakdown Review follows Sessions because it links orchestration-token Sessions into Session Reports; Project Task History follows so both Markdown intake and archive/history branches of the React Board stop exiting into Jinja. Alarms and Settings migrate after those primary Board journeys are coherent.

React Task Breakdown Review preserves every current editable contract field. Candidate decision fields remain immediately visible; detailed slicing evidence uses progressive disclosure. Global contract, constraints, verification, rejected items, non-goals, and recommended sequence remain visible alongside candidates. React must not reduce review to accept/reject cards that hide or drop contract data.

Pre-acceptance Task Breakdown edits remain browser-local. React warns before navigation when edits are unsaved. The server persists the reviewed breakdown and materializes accepted Tasks only after the operator explicitly chooses `Accept selected and estimate`; the migration does not add server-side draft/autosave state.

React Settings mutations stay on the current Settings surface. They show inline success or sanitized error feedback, then re-fetch authoritative state without discarding the operator's page/adapter/project context. Setup remains an explicit next-action link rather than a forced post-save redirect. Destructive actions still require confirmation.

Project Task History preserves bookmarkable status filters, estimate/actual/model evidence, Session Report links, Worker Run and blocker evidence, manual-estimate indicators, archive timestamps, and inline Unarchive behavior.

Normal React Login uses a standalone branded layout without authenticated Portal navigation. When Portal auth is disabled, `/login` redirects to the normal root. When the React build is unavailable, the minimal server-rendered Portal Recovery Surface provides login instead.

Successful login always opens the React Dashboard. The login flow does not preserve or accept a requested return URL.

When the React app has loaded, it owns branded not-found pages and recoverable data/action errors inside the normal Portal experience, with retry/navigation paths and sanitized messages. The server-rendered Portal Recovery Surface handles only frontend boot failure and fallback login; it is not the normal error renderer. Raw backend exception details must not reach operator-facing error UI.

Each migrated Jinja surface is frozen rather than extended once React owns its canonical route. It remains temporarily executable only as missing-build fallback and a parity oracle. After every normal surface, login, and recovery behavior passes final browser proof, a separate Jinja-retirement change removes all duplicated templates/routes/assets together, preserves only the Portal Recovery Surface, and adds an invariant test preventing normal routes from rendering retired templates.

Each numbered remaining migration slice is its own OpenSpec change and verification gate. Sessions list/report remain paired by explicit decision; no other slices are bundled by default. Sync and archive each completed change before proposing the next one.

Remaining migration targets desktop operator use only. Narrow-screen/mobile behavior is not an acceptance requirement and should not expand slice scope. Desktop pages must still avoid regressions against the existing Portal's table, form, and evidence readability.

Every desktop slice still requires practical accessible behavior: keyboard-operable controls, explicit labels, visible focus, semantic headings/tables, status and error announcements, non-color-only state, and correct confirmation-dialog focus handling. Formal accessibility certification is outside migration scope.

Remaining slices preserve the established React shell, design tokens, visual language, and component patterns. Functional and information parity come before visual reinvention. Page-specific readability fixes are allowed; new branding, a replacement design system, and broad animation or visual redesign are separate future work after Jinja retirement.

---

## Phase 6: Make React the Default Again

**Objective:** Re-enable React as the authenticated landing only after parity gates pass.

**Status:** Complete through `react-portal-default-enable`; the landing is build-aware and preserves Jinja fallback.

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
- Final frontend boundary: React owns every normal user-facing route, including login. A minimal server-rendered Portal Recovery Surface remains only for login and recovery when the React build is missing or partial; it does not retain duplicated operator workflows.
- Migrated React surfaces own existing canonical user-facing URLs. `/app` remains only a transitional alias and must not grow into a parallel route namespace.
- Final `/app/*` compatibility is redirect-only; canonical Portal URLs are the only rendered route tree.
- Sessions list and full Session Report migrate together as the first remaining read-only vertical slice.
- React Session Report preserves all existing summary and audit evidence; collapsible presentation is allowed, omission is not.
- React Sessions list auto-refreshes only while at least one session is active, then stops polling.
- Active Session Reports announce new evidence and require explicit refresh rather than replacing dense audit content mid-read.
- React Alarms exposes validated context-aware Continue, Abort Session, and Raise Budget actions; it does not expose generic raw Guardrail mutation.
- React Alarms defaults to Open and exposes bookmarkable Resolved/All audit history with resolution evidence.
- Budget, Control Plane, Worker, and Project Settings migrate as bounded changes before Setup Overview; Setup lands only after its destinations are React.
- Setup `Ready to launch` requires at least one launch-ready Connected Project; React must not copy the current optional-project drift.
- Correct the current Jinja Setup readiness claim in a small verified change before starting Sessions migration.
- React Settings actions remain on-page with inline outcomes and refreshed authoritative state; successful saves do not force navigation to Setup.
- Task Breakdown Review and Project Task History migrate before Alarms and Settings because they are direct branches of the primary React AGILE Board workflow.
- React Task Breakdown Review keeps full editable contract parity while using progressive disclosure for dense slicing evidence.
- Task Breakdown Review keeps pre-acceptance edits browser-local, warns before leaving, and persists only on explicit acceptance.
- React Login is a standalone branded screen; authenticated Portal chrome appears only after login.
- Successful login always opens Dashboard; no requested-page return target is preserved.
- React owns normal not-found and recoverable page errors; minimal server rendering handles only frontend boot failure and fallback login.
- Migrated Jinja pages freeze as temporary fallbacks; one separate final retirement change deletes all duplicated frontend surfaces after full parity proof.
- Every numbered remaining migration slice uses a separate OpenSpec change, verification gate, and archive boundary.
- Remaining React migration is desktop-only; mobile/narrow-screen redesign is outside scope.
- Each desktop slice requires practical keyboard, labeling, focus, semantic, and status-announcement accessibility; formal certification is outside scope.
- Remaining slices preserve the current React design system and prioritize functional parity over visual redesign.
