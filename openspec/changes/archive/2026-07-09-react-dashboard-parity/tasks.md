## 1. Shared dashboard state and authenticated JSON

- [x] 1.1 Extract the existing Jinja dashboard calculations in `src/agile_ai_htb/routes/portal.py` into one reusable private context helper without changing Jinja `/dashboard` behavior.
- [x] 1.2 Add authenticated `GET /api/dashboard` in `src/agile_ai_htb/routes/react_shell.py`; reuse the shared calculation and return only documented allowlisted fields, with newest-first previews capped at five active sessions and five unresolved alarms.
- [x] 1.3 Add backend tests for dashboard JSON auth, exact projection allowlists/order, current budget window, Worker/accounting totals, resolved-alarm exclusion, active-session and estimation-accuracy state, project entries, and absence of raw internal fields.
- [x] 1.4 Seed one dashboard fixture and assert the Jinja context and React JSON projection agree on budget totals/window, next actions, open alarms, active-session preview, and estimation accuracy.

## 2. React dashboard presentation

- [x] 2.1 Replace the `/app` project-picker-only view with `Dashboard` in `frontend/src/App.jsx`; retain exact React route ownership and existing workspace/board routes.
- [x] 2.2 Render dashboard next actions, KPIs, spend categories, native token-component disclosure, session/alarm previews, accuracy states, project entry cards, and actionable empty states from `/api/dashboard`; project cards use React `AppLink` while next-action, session, alarm, and full-board links remain Jinja anchors.
- [x] 2.3 Make Dashboard the sole active in-shell home sidebar `AppLink`; ensure `+ Open local repo` is not active on `/app`, and preserve project active states.
- [x] 2.4 Extend shared React CSS only for dashboard layouts and responsive behavior; reuse existing Portal tokens and primitives.

## 3. Regression coverage and verification

- [x] 3.1 Extend frontend SSR tests for `/app` dashboard routing, Dashboard as sole active home state, loading/error/empty rendering, in-shell project navigation, and full-page Jinja workflow links.
- [x] 3.2 Update `tests/portal/test_react_shell.py` source/contract assertions for the React dashboard while preserving root/login Jinja-default and missing-build coverage.
- [x] 3.3 Run `uv run pytest -q`, `npm --prefix frontend run check`, `openspec validate react-dashboard-parity --strict`, `openspec validate --specs --strict`, and `git diff --check`.