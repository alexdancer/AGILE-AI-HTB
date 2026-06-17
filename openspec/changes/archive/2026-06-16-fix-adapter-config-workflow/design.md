## Context

The AGILE-AI-HTB portal currently seeds four worker adapter presets (`opencode`, `claude_code`, `codex`, `hermes`) into the SQLite database at startup. These adapters have config templates but no working directory, no verification status, and no discovered models. The Workers settings page (`/settings/workers`) shows adapter state but provides no way to set the working directory — the prerequisite for all other operations (verification, model discovery, task launch). The only path to configure an adapter is through the Project connection flow, which auto-sets the `opencode` adapter's workdir when a local project is connected.

The board task launch flow is gated on `has_verified_worker_adapter()` — the "Launch task" button is hidden until an adapter passes verification. Since verification requires a workdir that can't be set through the UI, the board launch path is unreachable for new deployments.

This change adds the missing UI controls to the Workers page and removes the UX deadlock on the board.

**Current state diagram:**
```
Seed adapters → [workdir=NULL, unverified, models=[]]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            Workers page     Project connect    Direct API
            (no workdir      (sets opencode    (no UI)
             form, can't      workdir only)
             configure)
```

**Target state:**
```
Seed adapters → [workdir=NULL, unverified, models=[]]
                    │
                    ▼
            Workers page
            ┌───────────────────────────────┐
            │  Set workdir form             │
            │  Set as default button        │
            │  Diagnostics (all adapters)   │
            │  Discover models button       │
            │  Verify form                  │
            └───────────────────────────────┘
                    │
                    ▼
            Board launch
            ┌───────────────────────────────┐
            │  Adapter selector             │
            │  Model selector               │
            │  Launch button (always shown) │
            │  Inline error if not ready    │
            └───────────────────────────────┘
```

## Goals / Non-Goals

**Goals:**
- Operator can set a working directory for any adapter through the Workers page
- Operator can designate a default adapter for board launches
- All adapter kinds show installation diagnostics (not just OpenCode)
- Board launch form includes adapter and model selectors
- Board launch button is always visible for Estimated/Ready tasks; errors surface inline when adapter isn't ready
- Workers page does not run subprocesses on every render (cache diagnostics)

**Non-Goals:**
- Changing the adapter DB schema — `update_worker_adapter()` already supports all needed fields
- Adding a project-connection form to the board — project connection stays on the Project page
- Changing the proxy-governed vs native-usage decision flow — those options remain in the Verify form
- Adding a "create new adapter from scratch" flow — only presets are managed
- Modifying `task_launch.py` launch logic — it already accepts `adapter_id`/`model` params

## Decisions

### Decision 1: Workdir form on Workers page → POST to existing adapter update route

**Chosen:** Add a `<form>` per adapter card that POSTs `workdir` to a new endpoint `POST /settings/workers/{adapter_id}/configure`. The route calls `db.update_worker_adapter()` with the workdir value, then redirects back to `/settings/workers`.

**Alternative considered:** Reuse the existing `/settings/workers/{adapter_id}/verify` endpoint by cramming workdir into the verify payload. Rejected — verification is a separate operation with different semantics. Setting workdir should not trigger verification.

### Decision 2: Diagnostics for all adapters → call `detect_worker_adapter()` for every adapter, but cache

**Chosen:** On Workers page load, check `detect_worker_adapter()` for every adapter whose `kind` has a corresponding preset. Store the result in `adapter["config"]["_diagnostics"]` via `db.update_worker_adapter()` so it survives page reloads. Only re-run diagnostics if the cached result is >5 minutes old or if the operator clicks a "Refresh diagnostics" button.

**Alternative considered:** Run diagnostics on every page load for all adapters. Rejected — subprocess calls on every render would make the page unusably slow (4 adapters × ~2s each = 8s page load).

### Decision 3: Board launch adapter/model selectors → dropdowns populated from DB

**Chosen:** The board template receives a list of adapters (from `db.list_worker_adapters()`). The launch form adds `<select>` elements for adapter and model. The model dropdown is populated dynamically from the selected adapter's `supported_models`. This uses a small inline `<script>` for the client-side filtering.

**Alternative considered:** Separate the launch form into a modal or dedicated page. Rejected — overcomplicates a 2-field selection. Inline selectors on the board card keep the flow linear.

### Decision 4: Launch button always visible → error message when not ready

**Chosen:** Remove the `{% if has_verified_worker_adapter %}` gate from the board template. The launch button always renders for Estimated/Ready tasks. When clicked with no verified adapter, the `TaskLaunchBlocked` exception from `launch_task()` is caught by the route and rendered as an inline error on the redirect back to `/board`.

**Alternative considered:** Show the button but `disabled` with a tooltip. Rejected — disabled buttons are worse UX than clickable buttons with clear error feedback. The current exception flow already produces good error messages via `TaskLaunchBlocked.reasons`.

### Decision 5: Error feedback on board → flash message via query param

**Chosen:** When `launch_task()` raises `TaskLaunchBlocked`, the route redirects to `/board?error=...` with a URL-encoded error message. The board template reads `request.query_params.get("error")` and renders a dismissible error banner. The Reasons list is serialized as a semicolon-joined string.

**Alternative considered:** Use session cookies for flash messages. Rejected — adds complexity and the current auth cookie path. Query params are simpler and stateless.

## Risks / Trade-offs

- **Diagnostics caching staleness**: If an adapter binary is installed/removed between page loads, cached diagnostics may be stale. → Mitigated by "Refresh diagnostics" button and 5-minute auto-expiry.
- **Workdir validation**: The form accepts any string as workdir. If the path doesn't exist, verification will fail with a clear error — same as current behavior when workdir is set via project connect.
- **Client-side model filtering**: The inline `<script>` for dynamic model dropdown adds ~20 lines of JS. → Trade-off accepted; server-side model filtering would require an HTMX dependency or page reload, both worse UX.
