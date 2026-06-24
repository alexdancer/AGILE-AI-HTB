## Context

The portal is server-rendered FastAPI/Jinja. The dashboard currently shows budget, session, and alarm summaries. Task launch and review live on the board, while Worker setup lives under settings. Operators can complete the workflow, but the dashboard does not prioritize the next action.

## Goals / Non-Goals

**Goals:**
- Make the dashboard answer "what should I do next?"
- Reuse existing task, alarm, and adapter state.
- Link to existing pages instead of creating new flows.
- Keep the UI server-rendered with no new dependencies.

**Non-Goals:**
- No drag/drop board rewrite.
- No live updates or websocket notifications.
- No new workflow engine or persisted action queue.
- No changes to Worker Adapter launch semantics, model routing, or tracking modes.

## Decisions

1. **Derive next actions at request time.**
   - Use existing database reads in the dashboard route plus task and adapter summaries.
   - Alternative considered: persist dashboard action records. Rejected as unnecessary state for derived UI.

2. **Show actions as links to existing pages.**
   - Worker setup links to `/settings/workers`.
   - Launch/review work links to `/board`.
   - Alarm work links to `/alarms`.
   - Alternative considered: inline all controls on the dashboard. Rejected because it duplicates existing forms.

3. **Priority is advisory, not blocking.**
   - The panel highlights important actions but does not prevent navigation or task operations elsewhere.
   - Alternative considered: wizard-style forced flow. Rejected because experienced operators need direct access.

4. **Keep copy model-layer aware.**
   - Worker setup action refers to Worker adapters, not the control-plane model.
   - Task review/launch actions preserve existing board semantics.

## Risks / Trade-offs

- **Risk:** Counts drift if task status names change. → Mitigate by deriving from the same statuses the board already groups.
- **Risk:** Dashboard becomes noisy. → Mitigate by showing only a small ordered list of actionable rows.
- **Risk:** Operators expect dashboard buttons to perform actions directly. → Mitigate with clear link labels like "Open board" and "Open Worker setup".
