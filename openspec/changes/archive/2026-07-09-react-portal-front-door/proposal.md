## Why

The React Portal shell shipped in `introduce-react-portal-shell` is unreachable
through normal use: there is no front door into it and no project picker, so an
operator must hand-type `/app/projects/<id>` with a project id they already
know. The migrated workspace/board surfaces work, but nothing links to them.

This change makes the React shell the default authenticated landing and gives it
a project picker plus client-side navigation, so operators enter React by
logging in and clicking — never by typing URLs. It is the first step of the
larger goal of moving the entire Portal to React, and it deliberately ports no
new surfaces: it only makes what already exists reachable.

## What Changes

- Make the authenticated landing (root redirect and post-login) prefer the React
  shell when the frontend is built, falling back to the existing Jinja landing
  when the build is absent so a missing build never bricks the Portal.
- Add an authenticated JSON endpoint for the connected-project list, reusing the
  existing project-list and task-count helpers.
- Add a React home / project-picker view that lists connected projects with entry
  points into each project's workspace and board, plus an empty state that links
  to the existing connect-project flow.
- Add client-side (History API) navigation between the React home, workspace, and
  board so movement between them needs no manual URL entry, while deep links to
  `/app/*` still resolve on a full load.
- Keep the Jinja login page and every non-migrated Jinja surface working
  unchanged; login simply lands on the build-aware landing.

Non-goals (deferred to later slices of the full-React migration):

- No new migrated read surfaces (dashboard, sessions, session report,
  task-history, settings, setup, alarms stay server-rendered Jinja for now).
- No conversion of POST action routes from Jinja redirects to JSON responses.
- No deletion of Jinja templates/routes and no making the frontend build a hard
  prerequisite; the Jinja fallback stays as the safety net during migration.
- No React login/auth rewrite.

## Capabilities

### Modified Capabilities
- `react-portal-shell`: The React shell becomes the default authenticated
  landing (build-aware), gains a project-picker home, and navigates client-side
  between its surfaces, instead of being reachable only by manually typed
  `/app/*` URLs.

## Impact

- Updates the authenticated landing/root-redirect resolution to be build-aware.
- Adds one authenticated JSON endpoint for the connected-project list.
- Adds React home view and client-side navigation to the existing `frontend/`
  app; rebuilds the static bundle.
- Keeps all existing Jinja routes, templates, login, and POST action redirects
  unchanged as the migration safety net.
- Adds backend tests for the build-aware landing and the project-list endpoint.
