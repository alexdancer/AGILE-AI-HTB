## Context

The Jinja `/dashboard` route builds its view from budget, Worker token, alarm, session, task, adapter, and estimation helpers in `portal.py`. The React `/app` shell now has the same chrome as Jinja but only renders a project picker. Its sidebar Dashboard link is still a full-page Jinja anchor, so `/app` does not answer the operator's next-action question.

React must become dashboard-equivalent without becoming the backend authority. Root, login, and logout remain Jinja-directed because React still lacks AGILE Board functional parity.

## Goals / Non-Goals

**Goals:**
- Make explicitly visited `/app` a React dashboard with the same read-only operator intent as Jinja `/dashboard`.
- Reuse one backend dashboard calculation for Jinja and the authenticated React JSON handoff.
- Keep the JSON response bounded to fields rendered by the dashboard.
- Keep project access available through the React sidebar and dashboard entry cards.
- Prove auth, JSON shape, Jinja/React data agreement, and frontend route/render contracts.

**Non-Goals:**
- Do not make React the root/login/logout landing.
- Do not migrate Board intake, launch, refresh, queue, review, archive, or dismissal actions.
- Do not add polling, WebSockets, charts, Redux, a new persistence model, or a separate Node server.
- Do not expose raw Session, Worker Run, token-ledger, adapter-config, or secret-bearing records through dashboard JSON.

## Decisions

### Keep `/app` as the only React dashboard route

`/app` replaces its project-picker-only content with the dashboard. The existing exact FastAPI shell routes remain `/app`, `/app/projects/{id}`, and `/app/projects/{id}/board`; no `/app/dashboard` or `/app/projects` route is added.

The Dashboard sidebar item becomes an `AppLink` to `/app` and is the sole active home item on that route; `+ Open local repo` is not active. Project cards and the existing sidebar preserve React workspace/board entry without adding route inventory.

**Alternative:** Add `/app/dashboard` and retain the picker at `/app`. Rejected: it leaves two competing React homes and delays the stated `/app` front-door goal.

### Share dashboard calculation; project a safe JSON view

Extract the existing Jinja dashboard calculation in `portal.py` into a private reusable helper. The Jinja route keeps rendering `dashboard.html` from that helper. A new authenticated `GET /api/dashboard` route in `react_shell.py` lazily reuses the helper, then returns only the data needed by React:

- next actions;
- budget window, cap, total, and zone;
- Worker execution totals, status split, spend categories, and bounded component details;
- active-session preview rows (`id`, task description, model, status`), at most five newest active/running sessions first;
- open-alarm counts and recent-alarm preview rows (`id`, type, severity, session id, recommended action), at most five newest unresolved alarms first;
- estimation-accuracy summary;
- project-entry rows with identity, task count, capability summary, and React workspace/board targets.

The endpoint does not serialize raw DB dictionaries. Its response is an explicit allowlist: `next_actions` entries contain `label`, `detail`, `href`, and `tone`; session/alarm/project entries contain only the fields listed above (projects: `id`, `name`, `task_count`, and capability summary); summary objects contain only dashboard totals, status splits, component items, and accuracy fields rendered by the view. Existing `portal_template_context`, project view helpers, budget functions, and token-summary helpers remain sources of truth.

**Alternative:** Recalculate dashboard values independently in `react_shell.py`. Rejected: Jinja and React would drift on budget-window, alarm-resolution, and token-accounting semantics.

### React remains presentation-only

A `Dashboard` view loads `/api/dashboard` with the existing `useResource` hook. It renders summary cards, native `<details>` for token components, tables/empty states for sessions and alarms, estimation accuracy, and project entry cards. Project cards use `AppLink` for React workspace/board navigation; next-action, session, alarm, and full-board links use ordinary anchors for Jinja workflows until those surfaces reach parity. No React action wrapper is introduced.

**Alternative:** Add dashboard mutation JSON endpoints now. Rejected: board and alarm workflows are not part of this read-only phase.

### Test contracts at the API and rendered-surface boundaries

Backend tests cover auth rejection, exact projection allowlists/order, resolved-alarm exclusion, current budget window, Worker/accounting categories, and accuracy states. One seeded fixture compares the shared Jinja dashboard context with the React JSON projection for budget values, next actions, open alarms, active-session preview, and accuracy state. Frontend Node SSR tests cover `/app` routing, Dashboard as the sole active home item, loading/error/empty states, in-shell project links, and full-page workflow links. Existing build and FastAPI shell tests remain required.

## Risks / Trade-offs

- **Jinja/React data drift** → One shared calculation and API/Jinja agreement tests.
- **Dashboard JSON leaks internal evidence** → Explicit projection plus regression tests that assert raw/session-secret fields are absent.
- **Removing picker-only `/app` obscures project access** → Sidebar and dashboard project cards retain React workspace/board entry.
- **React looks complete while Board remains incomplete** → Dashboard actions link to Jinja workflows; root/login stay Jinja; no default-enable work is included.
- **Large dashboard response grows over time** → Return only bounded previews already rendered by the Jinja dashboard; detail pages remain authoritative.

## Migration Plan

1. Add the shared dashboard calculation and authenticated safe projection endpoint.
2. Replace React `/app` content with Dashboard and update sidebar routing/active state.
3. Add API, frontend rendering, and source/route regression tests.
4. Build React assets and run the existing shell/Jinja tests.

No data migration or deployment sequencing is required. If React dashboard rendering fails after deployment, `/dashboard`, root/login, and all non-migrated Jinja workflows remain available; revert the frontend route/view and dashboard endpoint without touching persisted state.

## Open Questions

None. The route and full read-only scope were agreed during exploration.