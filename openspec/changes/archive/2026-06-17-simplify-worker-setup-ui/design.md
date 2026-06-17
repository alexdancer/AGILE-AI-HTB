## Context

`/settings/workers` is currently the canonical Worker Adapter settings page, but its UI is shaped like an internal debug console. Each adapter card exposes workdir configuration, default selection, diagnostics, native model discovery, model entry, proxy URL, verification, and raw evidence. The portal also lacks a first-class budget setup surface, even though token budget governance is central to the product promise. That makes the first-run goal unclear: configure the budget, connect the project, verify one Worker Adapter, and make the AGILE Board launch-ready.

The standalone design reference for this broader setup flow is `docs/mockups/setup-flow-2099.html`. It models a setup overview, token budget setup, and simplified Worker setup using only synthetic DEMO 2099 values.

The product requirements still require first-class Worker Adapter presets and Launch Guardrails. This change simplifies the portal workflow without weakening the harness thesis: Worker launch remains blocked until adapter configuration and token-tracking verification are proven.

## Goals / Non-Goals

**Goals:**

- Turn Worker Setup into a guided one-active-adapter workflow.
- Add a setup overview that shows launch readiness across control-plane model, token budget, project connection, Worker verification, and Board launch state.
- Add a token budget setup surface for daily cap, per-session cap, and budget scope explanation.
- Make launch readiness obvious with a single status summary and actionable next step.
- Preserve first-class adapter presets for OpenCode, Claude Code, Codex, and Hermes.
- Preserve existing server-rendered portal architecture: FastAPI routes, Jinja templates, SQLite-backed adapter records.
- Hide low-level diagnostics/evidence behind Advanced details instead of removing them.
- Keep `/settings/workers` as the canonical route linked from board launch blockers.

**Non-Goals:**

- Do not add a frontend framework, JavaScript build pipeline, or SPA.
- Do not add provider-key management to Worker Setup; control-plane model auth remains environment-driven and separate.
- Do not treat local tokenizer estimates as authoritative token spend for budget enforcement.
- Do not remove adapter diagnostics, model discovery, verification evidence, or proxy-governed support from the backend.
- Do not make unverified adapters launchable for the sake of UX simplicity.
- Do not implement split Local Runner, hosted workspace, or tunnel runner behavior in this change.

## Decisions

### Decision: One active/default adapter as the primary setup surface

The page will show all supported adapter presets in a simple chooser, but the main setup form will focus on the selected active adapter. The selected adapter is the current default when one exists; otherwise it falls back to the first seeded adapter.

Rationale: first-run setup is about getting one Worker launch-ready, not comparing every adapter's internals. The default adapter is already the board's preferred launch choice, so anchoring setup around it matches the product workflow.

Alternative considered: keep all adapter cards visible but simplify each card. Rejected because it still presents too many repeated controls and does not establish a clear next action.

### Decision: Readiness summary drives the page

The top of the page will present a single launch-readiness state for the active adapter: launch-ready, not configured, model missing, verification missing, or verification failed. The page should surface the next corrective action in plain language.

Rationale: Launch Guardrails are a product feature, not a hidden backend error. The operator should understand why the AGILE Board can or cannot launch work.

Alternative considered: rely on colored pills per adapter. Rejected because pills are compact but not instructive.

### Decision: Setup overview owns first-run readiness

The portal will introduce a setup overview/checklist that shows the launch path as discrete gates: control-plane model connected, token budget configured, project connected, Worker token tracking verified, and Board launch enabled.

Rationale: Worker setup alone is not enough to explain readiness. The operator also needs to know whether budget governance is configured and whether the Board can safely launch a task.

Alternative considered: add only `/settings/budget` and keep setup distributed across settings pages. Rejected because the first-run experience would still require the operator to infer readiness from scattered pages.

### Decision: Budget setup distinguishes enforcement from visibility

Token budget setup will make the budget scope explicit: Worker launch guardrails are governed by `worker_execution` spend, while dashboard visibility can show total tracked spend across control-plane, task breakdown, adapter verification, reporting, and Worker execution categories.

Rationale: setup/estimation/reporting tokens are real tracked spend, but they should not unexpectedly consume the Worker execution budget that determines whether a coding task may launch.

Alternative considered: count every token category against launch budget. Rejected because control-plane setup and estimates could block useful Worker launch even when Worker execution budget remains available.

### Decision: LiteLLM remains a transport/accounting path, not the only tracking authority

Proxy-governed Worker mode and control-plane model calls can continue using LiteLLM for provider abstraction and usage extraction. Native Worker mode may instead rely on trustworthy native CLI usage evidence. If native usage evidence is unavailable, the run must be labeled observed-only/not budget-authoritative rather than treated as enforced spend.

Rationale: recent architecture separated control-plane and Worker models. The portal should reflect that separation and avoid forcing native local Worker setup through generic provider-key/LiteLLM assumptions.

### Decision: Keep raw/debug details under Advanced details

Diagnostics, executable path, command, proxy URL, tracking mode labels, model discovery JSON, and raw verification evidence remain available but collapsed behind an Advanced details section for the active adapter.

Rationale: these details are valuable for troubleshooting and tests, but they should not dominate the first-run setup flow.

Alternative considered: remove debug details entirely. Rejected because adapter setup failures often require evidence, and the project already has useful backend diagnostics.

### Decision: No new backend data model required for the first slice

The first implementation can derive the page view model from existing worker adapter rows: `is_default`, `workdir`, `supported_models`, `verification_status`, `verification_evidence`, `verified_at`, and cached diagnostics in adapter `config`.

Rationale: the problem is primarily presentation and flow. Avoid migrations unless implementation discovers a missing persisted state.

Alternative considered: add a dedicated Worker Setup state table. Rejected as premature.

### Decision: Keep Worker Adapter and control-plane model setup separate

Worker Setup configures coding-agent adapters. It must not ask for a generic provider API key or collapse control-plane model auth into Worker setup.

Rationale: AGILE-AI-HTB has separate model layers: the control-plane/orchestrator model powers estimates and reports, while Worker/coding harness models are selected through adapter setup and discovery. Merging them would recreate the provider-key confusion this project is trying to avoid.

## Risks / Trade-offs

- **Risk:** Hiding diagnostics could make failures harder to troubleshoot. → **Mitigation:** keep Advanced details visible on demand and preserve exact failure reason text.
- **Risk:** Focusing on one adapter may make other supported adapters feel less first-class. → **Mitigation:** keep all presets visible in the chooser with detected/verified/launchable status.
- **Risk:** Existing tests may assert debug-grid controls directly. → **Mitigation:** update tests around user-facing setup behavior and add coverage for Advanced details where needed.
- **Risk:** Current route handlers may not provide a clean readiness reason. → **Mitigation:** add a small view-model helper rather than spreading readiness logic through the template.
- **Risk:** The simplified page could imply native adapter mode is always launch-ready after install detection. → **Mitigation:** make token-tracking verification the explicit final gate before launch-ready status.
