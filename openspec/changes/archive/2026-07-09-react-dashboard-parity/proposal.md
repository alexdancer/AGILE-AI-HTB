## Why

The React shell now has Portal chrome but `/app` remains a project picker while the Jinja dashboard still answers the operator's first question: what needs attention now. Keeping those surfaces separate prevents `/app` from becoming a coherent operator front door and blocks later default-landing parity.

## What Changes

- Make the existing React-owned `/app` route render a dashboard-equivalent home instead of a project-picker-only view; it remains an explicitly visited, non-default route.
- Add a read-only authenticated dashboard JSON handoff derived from the same backend calculations as the Jinja dashboard, without duplicating budget, Worker, alarm, session, or estimation logic in React.
- Render full read-only dashboard parity in React: operator next actions, daily governed budget and Worker execution KPIs, spend breakdown and token component details, active sessions, open/recent alarms, estimation accuracy, and project entry cards.
- Make the React sidebar Dashboard item the sole active in-shell home link. Project entry cards use existing React workspace/board routes; dashboard next-action, session, alarm, and full-board links remain full-page Jinja anchors.
- Preserve Jinja `/dashboard`, root/login/logout Jinja landing behavior, build-missing fallback, and the exact three React shell routes. Do not add polling, charts, mutations, a new store, or a React Board promotion.

## Capabilities

### New Capabilities

<!-- None. This change extends existing Portal capabilities. -->

### Modified Capabilities

- `react-portal-shell`: add the React dashboard as the `/app` home, its authenticated JSON handoff, Dashboard sidebar routing/active state, and dashboard-equivalent read-only presentation while retaining Jinja workflow fallbacks.
- `portal-quality-system`: clarify that the Jinja dashboard remains available as a fallback after explicit React dashboard migration, while FastAPI remains authoritative and non-migrated Portal pages stay server-rendered.

## Impact

- **Frontend:** replace the `/app` project-picker view with a Dashboard view; update `App.jsx`, `Shell.jsx`, shared CSS, and frontend SSR tests. Project entry cards reuse existing React workspace/board links.
- **Backend:** add one authenticated read-only dashboard JSON endpoint in `react_shell.py`; extract/reuse the existing dashboard data calculation from `portal.py`; project only operator-safe dashboard fields into JSON.
- **Tests:** cover dashboard JSON auth, exact bounded projection shape/order, one seeded Jinja/API shared-state parity fixture, React route/sidebar sole-active contract, in-shell project links, full-page workflow links, and frontend rendering/build checks.
- **No schema/dependency changes:** no new persistence model, Node runtime, polling channel, chart library, or workflow action API.
- **References:** `docs/REACT_PORTAL_PARITY_PLAN.md` Phase 3 and `openspec/specs/react-portal-shell/spec.md`.