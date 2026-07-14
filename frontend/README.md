# Foreman AI HQ Portal frontend

A minimal [Vite](https://vitejs.dev/) + React shell for the Portal. It owns the
**home / project picker**, the project **workspace**, and the project **board
shell** as an explicit `/app` surface. The full FastAPI/Jinja Portal remains the
default authenticated landing while React parity work continues. Every other
Portal page stays server-rendered by FastAPI/Jinja.

FastAPI owns auth, persistence, estimation, launch guardrails, Worker Runs,
budget governance, and review disposition. This app only renders state from
authenticated JSON endpoints and submits actions to existing FastAPI routes; it
does not re-implement any of those rules.

## Build

The build writes static assets into `../src/foreman_ai_hq/static/react/`, which
FastAPI serves under `/static/react/`. No Node server runs in production.

```bash
cd frontend
npm install
npm run build      # or: npm run check
```

After building, start the app as usual. Logging in (or opening `/` with auth
disabled) still lands on the server-rendered Portal. Open `/app` explicitly to
use the React project picker. Navigation between its home, workspace, and board
is client-side (History API); these exact deep links resolve on a full load:

- `/app` — React home / project picker
- `/app/projects/<project_id>` — React project workspace
- `/app/projects/<project_id>/board` — React project board shell

Unknown `/app/*` paths return 404. If the build is missing, the three supported
React routes return a clear "frontend build missing" response instead of a
blank shell; the default server-rendered Portal remains usable.

## Develop

`npm run dev` starts Vite's dev server for fast iteration. Point API calls at a
running FastAPI instance (the JSON endpoints live under `/api/...`). Production
use does **not** require `vite` or `npm run dev`.
