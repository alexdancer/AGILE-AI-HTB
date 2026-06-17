## Why

The Worker Adapter configuration workflow through the portal is broken. Adapters are seeded into the database but cannot be configured through the UI — the Workers page has no form to set a working directory, making verification and model discovery impossible. The board's "Launch task" button is permanently hidden behind a verification requirement that can never be satisfied through the portal. The project-connected read-only proof flow works, but the standalone board intake → estimate → launch path is inaccessible.

## What Changes

- **Add workdir configuration to the Workers page** — a form to set the working directory for each adapter, enabling verification and model discovery
- **Add "Set as default" control** — allow operator to designate which adapter the board uses for launches
- **Extend diagnostics to all adapters** — not just OpenCode; show installation status for all seeded adapter kinds
- **Add adapter/model selection to the board launch form** — let operator pick which adapter and model to use when launching a task
- **Decouple board launch button visibility from verification** — show the button for Estimated/Ready tasks regardless, with clear error messages when adapter isn't ready
- **Remove blocking subprocess from Workers page load** — cache adapter diagnostics instead of running `--version` on every page render

## Capabilities

### New Capabilities
- `adapter-configuration-ui`: Workers page allows setting workdir, default adapter, and viewing diagnostics for all adapter kinds
- `board-launch-selection`: Board launch form includes adapter and model selectors, with inline error messaging

### Modified Capabilities
- `worker-adapters`: Diagnostics extend beyond just OpenCode; page-load performance improved by caching; launch button visibility decoupled from verification state

## Impact

- **`routes/portal.py`**: Workers route adds workdir/default form handling; board route passes adapter list
- **`templates/workers.html`**: Add workdir form, default button, diagnostics for all adapters
- **`templates/board.html`**: Add adapter/model selectors to launch form; remove verification gate on button visibility
- **`worker_adapters.py`**: No structural changes; diagnostics already handles all adapters — just need to call it for all
- **`db.py`**: No changes required; `update_worker_adapter()` already supports workdir/is_default
- **`routes/tasks.py`**: May need to accept adapter_id/model from launch form payload
- **`task_launch.py`**: No changes required; already accepts adapter_id/model parameters
