## 1. Build-aware front door

- [x] 1.1 Make the authenticated root redirect prefer the React shell when the frontend is built and fall back to the existing Jinja landing when the build is absent.
- [x] 1.2 Ensure successful login redirects through the same build-aware landing resolution.

## 2. Project list JSON handoff

- [x] 2.1 Add an authenticated JSON endpoint for the connected-project list, reusing existing project-list and task-count helpers, with no new schema.

## 3. React home and navigation

- [x] 3.1 Add a React home / project-picker view that lists connected projects with entry points into each project's workspace and board.
- [x] 3.2 Add an actionable empty state on the home that links to the existing connect-project flow when no projects exist.
- [x] 3.3 Add client-side (History API) navigation between home, workspace, and board without manual URL entry, preserving full-load deep links to `/app/*`.
- [x] 3.4 Keep links from the React shell to non-migrated Jinja surfaces working as full navigations.

## 4. Verification

- [x] 4.1 Add backend tests for the build-aware landing (built → React, missing build → Jinja fallback) and for project-list JSON auth and shape.
- [x] 4.2 Add/refresh the frontend build check for the new home view and navigation.
- [x] 4.3 Run `openspec validate react-portal-front-door --strict`, the frontend build check, and `uv run pytest`.
