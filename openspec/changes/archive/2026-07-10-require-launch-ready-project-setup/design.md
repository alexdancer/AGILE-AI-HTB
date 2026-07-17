## Context

`setup_overview` builds four readiness steps but currently computes `ready_to_launch` from only the first three: Control Plane, Token Budget, and Worker Adapter. Connected Projects are marked optional using raw project existence, not evaluated Project Capability. `_next_setup_step` also ignores the project step, and its ready destination uses the global `/board` shim, which selects the first connected project even if another project is the launch-ready one.

Project Capability already provides the authoritative `launch_ready` distinction through the Local Execution Backend. This change should consume that existing projection rather than duplicate Launch Guardrail rules.

## Goals / Non-Goals

**Goals:**

- Make Setup Overview's overall launch-ready claim truthful.
- Require at least one Connected Project whose computed capability state is `launch_ready`.
- Preserve current blocker priority: Control Plane, Token Budget, Worker Adapter, then Connected Project.
- Link the ready action to a specific launch-ready project's board.
- Cover no-project, non-launch-ready-project, and launch-ready-project states with focused tests.

**Non-Goals:**

- Change Project Capability or Launch Guardrail calculation.
- Change Worker Adapter readiness semantics.
- Change database schema, public APIs, or project connection behavior.
- Migrate Setup Overview to React or redesign its layout.
- Require every Connected Project to be launch-ready.

## Decisions

### Use computed Project Capability, not project existence

Setup Overview will require an available Local Execution Backend, obtain project view models through the existing live capability-aware projection, and select projects whose capability state equals `launch_ready`. When Local Runner is disabled and `_local_backend` returns `None`, no project may qualify from its persisted capability value. Raw `db.list_connected_projects()` existence and stored capability are insufficient because backend availability, analysis-only state, and blocked state determine whether governed work can execute now.

Alternative considered: duplicate the required path/backend/adapter/model checks in `setup_overview`. Rejected because Project Capability already owns that contract and duplicated checks would drift.

### Keep ordered next-action priority

The four setup steps remain ordered Control Plane, Token Budget, Worker Adapter, Connected Project. Overall readiness requires all four. `_next_setup_step` considers the project step after earlier blockers are resolved, so an operator with no launch-ready project is directed to `/settings/project`.

Alternative considered: show separate “Harness configured” and “Launch ready” states. Rejected for this bounded fix because the current surface claims launch readiness and the approved domain contract requires a launch target.

### Link to the selected launch-ready project board

When setup is complete, the primary action links directly to `/projects/{project_id}/board` for a computed launch-ready project. This avoids the global `/board` shim selecting an earlier non-launch-ready project.

Selection remains deterministic using the existing connected-project order; only launch-ready candidates participate.

### Keep the change server-rendered and state-free

The existing Setup template continues rendering the route context. No persistence or new API response is added. Copy changes are limited to replacing optional-project language with launch-readiness guidance where necessary.

## Risks / Trade-offs

- [Capability probes may be more expensive than raw project listing] → Reuse the existing bounded `_project_view_models` path only when Local Runner is available; do not add extra scans.
- [Persisted capability can be stale after Local Runner is disabled] → Require a live backend before accepting any computed `launch_ready` project and test that stale stored state cannot enable Setup readiness.
- [A project can lose capability after the page renders] → Setup remains a point-in-time summary; Launch Guardrails still re-check at launch.
- [Multiple launch-ready projects require a deterministic destination] → Use existing connected-project order and link the first launch-ready candidate explicitly.
- [Tests may accidentally depend on local machine CLI state] → Use a controlled backend fake for defensive `analysis_ready` projection coverage, a real invalid-path project for reachable `blocked` behavior, and existing database helpers for adapter evidence; do not invoke real Worker CLIs.
