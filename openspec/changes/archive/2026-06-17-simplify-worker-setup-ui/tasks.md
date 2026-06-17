## 1. Setup flow prototype and view model

- [x] 1.1 Review `docs/mockups/setup-flow-2099.html` and choose the final production route names for setup overview, token budget, and Worker setup.
- [x] 1.2 Inspect current `/settings/workers` route, adapter records, budget config loading, dashboard usage summary, and portal tests to identify existing expectations.
- [x] 1.3 Add a small setup overview view-model helper that reports control-plane readiness, budget setup readiness, project readiness, Worker verification readiness, and Board launch readiness.
- [x] 1.4 Add a small Worker Setup route/view-model helper that selects the active adapter from the default adapter or first seeded adapter.
- [x] 1.5 Add readiness summary data for the active adapter: launch-ready state, user-facing reason, and next action.
- [x] 1.6 Preserve existing diagnostics cache behavior and expose diagnostics/evidence for Advanced details without running extra subprocesses on normal page load.

## 2. Token Budget setup UI

- [x] 2.1 Add persistent storage for portal-configured daily token cap, per-session token cap, and budget confirmation state, or document why an existing settings store is sufficient.
- [x] 2.2 Add a Token Budget settings route and template that lets operators view and save daily/session token caps.
- [x] 2.3 Explain budget scope in the UI: `worker_execution` governs launch budget; all tracked categories contribute to dashboard visibility.
- [x] 2.4 Update dashboard/setup summaries to show Worker execution usage separately from orchestration/setup usage.
- [x] 2.5 Ensure saved portal budget values are used by budget zone calculation and budget alarm logic where appropriate.

## 3. Guided Worker Setup UI

- [x] 3.1 Replace `src/agile_ai_htb/templates/workers.html` card grid with a guided Worker Setup layout focused on one active adapter.
- [x] 3.2 Show all first-class adapter presets in a chooser/status area with detected/verified/launchable indicators.
- [x] 3.3 Provide primary setup controls for active adapter: project folder/workdir, save/set default, discover models, model selection, and verify token tracking.
- [x] 3.4 Move raw diagnostics, proxy URL/tracking-mode details, model discovery JSON, and verification evidence into an Advanced details disclosure.
- [x] 3.5 Ensure the primary UI does not ask for generic provider API keys or imply native Worker setup requires `PROVIDER_API_KEY`.

## 4. Board integration

- [x] 4.1 Update board launch error rendering so adapter setup/verification/budget failures include links to the relevant setup page.
- [x] 4.2 Verify the board still shows launch controls for Estimated/Ready tasks and surfaces Launch Guardrail failures inline.

## 5. Tests and verification

- [x] 5.1 Add/verify prototype checks for `docs/mockups/setup-flow-2099.html` if a static mockup validation convention exists.
- [x] 5.2 Update portal tests for setup overview and Token Budget setup: current values render, valid save persists, and category explanation is visible.
- [x] 5.3 Update portal tests for guided Worker Setup: active/default adapter selection, readiness summary, workdir save, default save, and Advanced details availability.
- [x] 5.4 Update or add tests for board launch errors linking to Worker Setup or Token Budget setup when launch readiness is incomplete.
- [x] 5.5 Run targeted portal tests covering setup overview, Token Budget setup, Worker Setup, and board launch behavior.
- [x] 5.6 Run the full test suite with `uv run python -m pytest -q`.
