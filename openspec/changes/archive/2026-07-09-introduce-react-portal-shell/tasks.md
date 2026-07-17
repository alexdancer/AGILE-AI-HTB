## 1. Frontend scaffold

- [x] 1.1 Add a minimal `frontend/` Vite React app with build/dev scripts and no UI framework beyond React.
- [x] 1.2 Move or duplicate only the shared visual tokens needed for the first migrated workspace/board shell.
- [x] 1.3 Add repository documentation or package metadata for the frontend build command.

## 2. FastAPI shell serving

- [x] 2.1 Add FastAPI static serving for built React assets from a deterministic build directory.
- [x] 2.2 Add explicit handling for missing React build assets so migrated routes do not render a blank shell.
- [x] 2.3 Keep non-migrated Jinja pages and login/auth redirects working unchanged.

## 3. Project workspace and board JSON handoff

- [x] 3.1 Add authenticated JSON state for the selected project workspace using existing project summary/readiness helpers.
- [x] 3.2 Add authenticated JSON state for the selected project board using existing board/task/queue/review evidence helpers.
- [x] 3.3 Ensure React task actions call existing backend action paths or thin JSON wrappers without duplicating guardrail, budget, launch, or review rules.

## 4. React workspace/board shell

- [x] 4.1 Implement the React project workspace view with project identity, readiness summary, action links, and board entry.
- [x] 4.2 Implement the React project board shell with scoped columns, compact task cards, empty states, queue/run status, and existing launch/review controls.
- [x] 4.3 Preserve links from the React shell back to non-migrated Jinja setup, settings, sessions, alarms, dashboard, and history pages.

## 5. Verification

- [x] 5.1 Add backend tests for React asset serving, missing-build behavior, auth on JSON endpoints, and Jinja fallback availability.
- [x] 5.2 Add the smallest frontend build check available for the Vite React app.
- [x] 5.3 Run `openspec validate introduce-react-portal-shell --strict`, frontend build check, and `uv run pytest`.
