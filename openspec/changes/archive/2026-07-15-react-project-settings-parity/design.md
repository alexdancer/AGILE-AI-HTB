## Context

Project Settings is Phase 5 slice #8, the fourth destination Settings surface after Budget, Control Plane, and Worker. The current surface is `templates/project.html` + `portal.py`:

- `GET /settings/project` (`portal.py:1437`) lists connected projects with `backend.project_capability`, lists archived projects, reports Local Runner `backend.status()` and `local_runner_enabled`, and renders `project.html`. The page shows each project's `root_path`, capability state, and capability reasons.
- Mutations:
  - `POST /settings/project/connect` (`:1464`) — connect a repo. Already negotiates JSON: `{project}` on success, `{detail}` on error, HTML redirect for form callers.
  - `POST /settings/project/{id}/read-only-proof` (`:1487`) — launches a read-only proof Worker task via the Local Runner. JSON-only live action returning the launch result or a guardrail block.
  - `POST /projects/{id}/archive` (`:634`) — archive a connected project. HTML `303` redirect only, with a block-reason guard that redirects to `/settings/project?error=`.
  - `POST /projects/{id}/restore` (`:648`) — restore an archived project. Already negotiates JSON via `_react_restore_outcome` (added for the React Workspace view).

The domain rules (connection, capability evaluation, archive/restore, read-only proof) live in `project-workspace`. So this slice is transport (`react-portal-shell`): a bounded JSON read, one negotiated outcome for the redirect-only `archive`, and a React view — mirroring the Worker and Control Plane slices. The `/projects` list and `/projects/{id}` workspace are out of scope; `restore` already serves the React Workspace, so no restore changes are needed here.

## Goals / Non-Goals

**Goals:**
- React owns `/settings/project` when the complete build exists; Jinja renders it otherwise, same URL.
- A bounded authenticated JSON read reusing the existing backend/capability builders; sanitized capability/backend evidence.
- Content-negotiated sanitized outcome for `archive`; HTML redirects (including the block-reason redirect) preserved.
- Connect, restore, and read-only-proof JSON contracts consumed unchanged.
- React parity for the connect form, backend-status panel, per-project capability, read-only-proof action, and archive/restore.

**Non-Goals:**
- No change to connection, capability, archive/restore, or read-only-proof logic.
- No new mutation routes; no schema migration.
- No `/projects` list, `/projects/{id}` workspace, or Setup migration.
- No deletion of `project.html`.
- No mobile/narrow-screen redesign.

## Decisions

- **Reuse the Settings pattern.** JSON read in `react_shell.py` guarded by `require_portal_auth`; negotiate the `archive` outcome on the existing `portal.py` route with `_wants_react_json`; build-aware GET via the shared `_react_index()`. No new mutation routes.
- **Reuse the existing builders for the read.** The JSON endpoint calls `_local_backend`, `db.list_connected_projects` / `db.list_archived_connected_projects`, and `backend.project_capability` — the same computation the Jinja page uses — so React never recomputes capability rules.
- **`root_path` is intentionally surfaced, not a leak.** The Jinja settings page already shows each project's `root_path` because the operator needs to see which local folder is connected. The JSON read exposes it deliberately for parity. This is distinct from the Worker-diagnostics `executable` path, which was an internal detection detail and was stripped; `root_path` is operator-facing configuration.
- **Bounded, sanitized capability/backend evidence.** Capability `reasons` and `backend_status` are bounded and passed through the shared evidence-safety helper so no raw exception text reaches the browser; only an allow-listed projection is serialized.
- **Live read-only-proof unchanged; React consumes it.** The proof action already returns a JSON launch/guardrail outcome. React posts it, shows the inline result, and refetches the read for authoritative capability state. No change to that route keeps the slice lazy.
- **The redirect-borne `?error=` must be forwarded, not dropped.** `/projects` stays Jinja in this slice and its archive form posts HTML, so a blocked archive still redirects to `/settings/project?error=<reason>` — a URL React now serves. React therefore forwards the param to the JSON read rather than rendering it from the URL, so the backend's existing sanitization/bounding still applies and the operator sees the same reason the Jinja page showed. Without this the reason would vanish silently, which would be a parity regression caused by migrating this surface ahead of `/projects`.
- **Archive negotiation preserves the block-reason redirect for HTML.** `archive` currently redirects to `/settings/project?error=<block_reason>` when archiving is blocked, and to `/projects` on success. HTML callers keep both redirects; JSON callers get a bounded `{ok, error}` outcome (sanitized block reason on failure) and React refetches.

## Risks / Trade-offs

- **Shared archive/restore routes.** `archive` and `restore` are project-level routes also reachable from other surfaces. `restore` already negotiates JSON for the Workspace view; adding JSON negotiation to `archive` must not change its HTML redirect behavior for any existing caller. Tests assert the HTML redirects (success `/projects`, blocked `/settings/project?error=`) are unchanged.
- **Route-ownership enumeration reconciliation.** The landing requirement's ownership sentence and its "Non-migrated and fallback Jinja routes remain reachable" scenario listed "Settings" as non-migrated and forbade any React client route from claiming it — which the prior three Settings slices left standing while claiming `/settings/budget`, `/settings/control-plane`, and `/settings/workers`. With this slice all four destination Settings surfaces are React, so this slice performs that reconciliation instead of deferring it again: the delta MODIFIES the landing requirement to name the four canonical Settings routes as React-owned, and rewrites the non-migrated clause to defer "what is migrated" to the per-surface requirements rather than re-enumerating surfaces that drift. Settings links stay ordinary full-page navigation, so the workspace requirement's "Project settings SHALL remain ordinary full-page links" is unaffected.
- **Sidebar Settings highlighting was unspecified.** The chrome requirement's active-marking prohibition is scoped to the project workspace/board routes, so it never contradicted the Settings highlighting the prior slices shipped — but no scenario stated the intended behavior either. The delta MODIFIES the chrome requirement to add the Settings-route highlighting scenario, closing the gap for the group this slice completes.
- **`root_path` disclosure.** Surfacing the local path is intentional parity, but the read must still be authenticated (`require_portal_auth`) so an unauthenticated caller cannot enumerate connected paths. Tests assert auth is required.
- **Read-only-proof latency.** The proof launches a real Worker task and can be slow. React shows a busy state and disables the action while in flight; it does not poll or add optimistic state — the authoritative read after completion is the source of truth.
