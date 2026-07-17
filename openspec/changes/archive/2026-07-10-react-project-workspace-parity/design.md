## Context

The React Portal currently owns `/app`, `/app/projects/{project_id}`, and `/app/projects/{project_id}/board`. Dashboard and board parity are complete, but `frontend/src/views/Workspace.jsx` renders only a reduced project summary. The Jinja workspace remains the richer source surface: it shows archive state, capability reasons, action links, and repo profile details. The React workspace also renders a board link for archived projects and passes backend attention URLs through unchanged, which can send operators back to Jinja for a workflow already migrated into React.

FastAPI already provides the authoritative project view model and `project_workspace_summary()` calculation. Project archive state, capability readiness, board launch safety, task counts, and workflow routes must remain backend-owned. The change must not alter the default landing, which remains Jinja until a later explicit React default-enable change.

## Goals / Non-Goals

**Goals:**

- Give the React workspace the same operator-facing project identity, readiness, action-summary, profile, and archive behavior as the Jinja workspace.
- Replace the current broad workspace handoff with a stable allowlisted JSON contract.
- Keep active project board navigation inside React while preserving ordinary full-page navigation for non-migrated pages.
- Make archived project direct access restore-first and launch-safe.
- Preserve current backend helpers, project IDs, archive metadata, task/session history, and workflow ownership.
- Verify auth, projection boundaries, active/archived states, navigation, and frontend rendering.

**Non-Goals:**

- No React `/app/projects` list or repo connection flow; existing `/projects` remains authoritative.
- No React migration of Sessions, Task history, Setup, Settings, Alarms, or Task Breakdown Review.
- No default root/login/logout routing change.
- No database/schema migration, new project table, or new generic mutation API.
- No duplicated capability, archive, launch, board, Worker Adapter, model, budget, or token-accounting logic in React.
- No SPA dependency, state-management library, WebSocket layer, or optimistic lifecycle transitions.

## Decisions

### Use a dedicated bounded workspace projection

Keep `GET /api/projects/{project_id}/workspace` as the authenticated handoff, but project its response explicitly instead of returning the complete internal project view model. The top-level keys are exactly `project`, `summary`, `controls`, and `links`:

```text
project
  id: string (128)
  name: string (200)
  root_path: string (4096)
  archived_at: string|null (64)
  capability
    state: string (64)
    label: string (200)
    reasons: string[] (20 items, 1000 each)
  profile
    git_branch: string|null (500)
    language_hints: string[] (20 items, 200 each)
    framework_hints: string[] (20 items, 200 each)
    package_manager_hints: string[] (20 items, 200 each)
    test_command: string|null (4000)
    run_command: string|null (4000)
    relevant_docs: string[] (50 items, 1000 each)
summary
  counts: {Estimated, Running, Review, Done, Blocked} non-negative integers
  total_tasks: non-negative integer
  launch_ready: boolean
  capability_state: string (64)
  attention_actions: [{label, detail, href, tone}] (20 items)
controls
  can_open_board: boolean
  can_restore: boolean
links
  board_href: string|null
  task_history_href: string
  sessions_href: string
  worker_setup_href: string
  project_settings_href: string
  restore_href: string|null
```

Attention action bounds are `label` 200, `detail` 1000, `href` 2048, and `tone` 32. Allowed generated hrefs are the selected React board, selected Jinja task history, `/sessions`, `/settings/workers`, and `/settings/project`; unknown helper hrefs are dropped rather than forwarded. `board_href` is exactly `/app/projects/{id}/board` only for active projects. `restore_href` is exactly `/projects/{id}/restore` only for archived projects.

All browser-visible strings are sanitized/redacted before truncation. Wrong nested types produce typed safe defaults (`null`, empty list, empty bounded string, `false`, or zero) instead of a 500. Unknown extra keys are never serialized. Values come from `_project_view_model()` and `project_workspace_summary()` plus existing project data. This avoids frontend rules and prevents future project metadata from becoming browser-visible by accident.

**Alternative:** Return the current project dictionary and let React select fields. Rejected: it makes the browser contract broad and unstable, and can expose internal profile/configuration fields.

**Alternative:** Add a new `/api/...` workspace endpoint. Rejected: the existing authenticated endpoint already owns the correct route and helper integration.

### Keep backend route semantics authoritative

Project lookup, unknown-project 404 behavior, capability calculation, archive visibility, and board restore-first safety remain in FastAPI. React only renders the projection and chooses links. The existing Jinja workspace remains available for fallback and non-migrated workflows.

For Restore from an archived React workspace, use the existing `POST /projects/{project_id}/restore` action with explicit representation negotiation:

- `Accept: application/json` selects a JSON response whose top-level keys are exactly `ok`, `error`, `next_href`, `retry_href`, and `project`.
- Success and already-active idempotent success return `200`, `ok: true`, `error: null`, `next_href: /app/projects/{id}`, `retry_href: null`, and `project: {id, archived: false}`.
- Unknown project returns `404`, `ok: false`, sanitized `error` (1000), `next_href: null`, `retry_href: /projects`, and `project: null`.
- Requests without explicit JSON negotiation preserve the current `303` redirect to `/projects/{id}` for both archived and already-active projects.

The JSON outcome is a thin response wrapper around existing restore semantics, not a second restore implementation. It never returns the project record or raw exception payload. React refetches workspace/sidebar state only after success.

### Use route-safe links by ownership

- `/app/projects/{id}/board` uses `AppLink` and stays in-shell.
- `/projects/{id}/task-history`, `/sessions`, `/settings/workers`, and `/settings/project` remain ordinary full-page Jinja links.
- Backend attention actions that target the migrated board are projected with the React board href. Labels/details still come from the shared workspace summary helper.
- Archived workspaces retain history/evidence and Restore links but do not show active board or launch entry points.
- Direct archived React-board access shows the archived state and routes the operator to `/app/projects/{id}` for Restore; it does not send the operator through a misleading active-board link.

This prevents the React workspace from silently falling back to Jinja for the main migrated board loop while avoiding duplicated non-migrated pages.

### Render summary before repo details

The React workspace shows project name, archive/readiness state, counts, and attention actions first. Repo profile data appears in a secondary panel, matching the Portal readability rule: operator action and launch state first, identity/evidence details second. Missing scalar values render a concise unavailable state; missing collections render an empty state rather than `undefined` or raw JSON.

### Refresh from authoritative state after Restore

React does not optimistically mark a project active. After a successful Restore outcome, it refetches the workspace and sidebar data so archive state, board availability, project visibility, and capability state come from FastAPI. On a `404` envelope or transport/server failure it does not refetch or alter the current archived state; it shows bounded error text, keeps Restore available when the current workspace exists, and uses the envelope `retry_href` only as an operator navigation option.

## Risks / Trade-offs

- **Risk:** Workspace JSON still leaks new internal project fields later → **Mitigation:** fixed nested allowlists and exact-key tests.
- **Risk:** Archived projects regain active controls through a frontend condition bug → **Mitigation:** backend projection sets `can_open_board: false` and `board_href: null`, backend board route remains restore-first, and tests cover workspace plus direct archived-board access.
- **Risk:** Attention actions regress to Jinja URLs → **Mitigation:** explicit route-owned links in the projection plus frontend assertions for React board hrefs.
- **Risk:** Restore behavior differs between React and Jinja callers → **Mitigation:** preserve HTML redirects and add only negotiated JSON outcomes for explicit React requests.
- **Risk:** Added profile details make workspace cards noisy → **Mitigation:** summary-first layout, secondary profile panel, bounded strings/lists, no raw evidence dump.
- **Risk:** Existing dirty worktree obscures scope → **Mitigation:** inspect targeted diffs before implementation and stage no unrelated files.

## Migration Plan

1. Add the bounded workspace projection and auth/shape tests without changing Jinja behavior.
2. Add the mandatory negotiated Restore JSON protocol, preserving HTML redirects.
3. Update React workspace rendering, archive controls, profile section, action links, and authoritative refetch behavior.
4. Add frontend contract tests and browser smoke coverage for active, archived, missing, loading, and error states.
5. Run targeted tests, frontend check/build, full `uv run pytest`, strict OpenSpec validation, and `git diff --check`.
6. Keep the change active until verification passes; sync/archive separately according to the OpenSpec workflow.

Rollback is limited to restoring the prior React workspace view and projection contract. Jinja routes, project data, archive records, board workflows, and default landing remain unaffected.

## Open Questions

None. Restore negotiation, projection keys/bounds/defaults, route ownership, and archived-board behavior are specified above.
