# AGILE-AI-HTB Portal frontend

A minimal [Vite](https://vitejs.dev/) + React shell for the Portal. It is the
first migrated Portal surface: the project **workspace** and project **board
shell**. Every other Portal page stays server-rendered by FastAPI/Jinja.

FastAPI owns auth, persistence, estimation, launch guardrails, Worker Runs,
budget governance, and review disposition. This app only renders state from
authenticated JSON endpoints and submits actions to existing FastAPI routes; it
does not re-implement any of those rules.

## Build

The build writes static assets into `../src/agile_ai_htb/static/react/`, which
FastAPI serves under `/static/react/`. No Node server runs in production.

```bash
cd frontend
npm install
npm run build      # or: npm run check
```

After building, start the app as usual and open a migrated route:

- `/app/projects/<project_id>` — React project workspace
- `/app/projects/<project_id>/board` — React project board shell

If the build is missing, `/app/*` returns a clear "frontend build missing"
response instead of a blank shell, and the server-rendered pages at
`/projects/<id>` and `/projects/<id>/board` remain available.

## Develop

`npm run dev` starts Vite's dev server for fast iteration. Point API calls at a
running FastAPI instance (the JSON endpoints live under `/api/...`). Production
use does **not** require `vite` or `npm run dev`.
