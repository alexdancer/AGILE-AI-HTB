## Why

The current Worker adapters page exposes adapter internals as a dense debug grid: workdir, default selection, diagnostics, model discovery, verification, proxy URL, and raw evidence all compete for attention per adapter. At the same time, the portal does not provide an obvious way to configure the token budget that Launch Guardrails govern against. First-run setup should instead guide the operator toward one concrete outcome: configure budget governance and make a Worker Adapter launch-ready without hiding the token-tracking verification gate.

## What Changes

- Add a setup overview/prototype flow that frames launch readiness as: control-plane model connected, token budget configured, project connected, Worker tracking verified, board launch enabled.
- Add a Token Budget setup surface so operators can configure daily and per-session token caps from the portal instead of editing `guardrails.yaml` by hand.
- Replace the current multi-card Worker adapters page with a simplified Worker Setup workflow focused on one active/default adapter at a time.
- Present setup as a short sequence: choose coding agent, set project folder/workdir, discover/select model, verify governed launch/token tracking.
- Keep Claude Code, Codex, OpenCode, and Hermes visible as first-class Worker Adapter presets, but do not show all low-level diagnostics on the default view.
- Move raw diagnostics, command/executable details, proxy URL, tracking mode labels, model discovery JSON, and verification evidence into an Advanced details section.
- Preserve Launch Guardrails: an adapter is not launch-ready until budget setup, adapter configuration, model compatibility, workdir validity, and token-tracking verification pass.
- Keep `/settings/workers` as the canonical Worker Setup route; this is a portal UX simplification, not a new product surface.
- Add `docs/mockups/setup-flow-2099.html` as the standalone design reference for the setup overview, budget setup, and Worker setup flow.

## Capabilities

### New Capabilities

- `guided-worker-setup`: Covers the simplified one-active-adapter Worker Setup workflow, user-facing readiness state, and advanced/debug detail disclosure.
- `token-budget-setup`: Covers portal-based budget cap configuration, budget scope explanation, category breakdown, and first-run readiness participation.

### Modified Capabilities

- `adapter-configuration-ui`: Changes the Workers settings UI requirement from a per-adapter debug-card grid to a guided setup page while preserving adapter configuration, default selection, diagnostics refresh, model discovery, and verification behavior.
- `board-launch-selection`: Updates board expectations to point users to the simplified Worker Setup flow when an adapter is not launch-ready.

## Impact

- `src/agile_ai_htb/templates/workers.html`: Replace dense card grid with guided setup layout and Advanced details disclosure.
- `src/agile_ai_htb/templates/base.html`: Add navigation for setup overview and token budget when implemented.
- `src/agile_ai_htb/templates/budget.html` or equivalent: Add budget setup form and category explanation.
- `src/agile_ai_htb/templates/setup.html` or equivalent: Add first-run setup overview/checklist.
- `src/agile_ai_htb/routes/portal.py`: May need small view-model changes to identify the active/default adapter, readiness status, and user-facing failure reason.
- Budget persistence: May need a small persisted portal budget setting or equivalent override path so budget setup survives process restarts.
- `tests/test_portal.py` and related Worker Setup tests: Update expectations from per-card debug controls to guided setup behavior.
- `openspec/specs/adapter-configuration-ui/spec.md` and `openspec/specs/board-launch-selection/spec.md`: Update product requirements to match the simplified setup flow.
- No new frontend framework or JavaScript build system; keep server-rendered Jinja/HTML consistent with the existing portal.
