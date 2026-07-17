## Why

React now has verified parity for Portal chrome, Dashboard, project workspace, and the normal governed AGILE Board lifecycle, but authenticated root and login still route operators to the temporary Jinja-first landing. Enable the planned React front door now while preserving usable Jinja fallback when the built shell is unavailable and full-page access to non-migrated workflows.

## What Changes

- Route the normal authenticated Portal landing to `/app` when the complete React build is available.
- Route successful auth-required login and auth-disabled local root/login flows through the same build-aware landing decision.
- Fall back to the existing Jinja project landing when the React index or any referenced build asset is missing; never send an operator to a `503` or blank shell as the default landing.
- Keep `/login`, logout semantics, explicit React deep links, existing Jinja project/dashboard/board routes, and full-page links to Sessions, Alarms, Setup, Settings, task history, reports, and Task Breakdown Review.
- Add routing and browser-smoke regression coverage for auth-required, auth-disabled, built, missing-build, partial-build, deep-link, and fallback-link behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `react-portal-shell`: Promote the verified React shell to the normal authenticated landing through a build-aware fallback gate while retaining Jinja support for non-migrated and unavailable-build paths.

## Impact

- Routing helpers and login/root/logout handlers in `src/agile_ai_htb/routes/portal.py` and build-readiness helpers in `src/agile_ai_htb/routes/react_shell.py`.
- React shell routing tests in `tests/portal/test_react_shell.py` plus frontend/browser smoke evidence.
- Durable default-landing contract in `openspec/specs/react-portal-shell/spec.md`.
- No persistence schema, API payload, Worker Adapter, governance, token-accounting, or dependency changes.
