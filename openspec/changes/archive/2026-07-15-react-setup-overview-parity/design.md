## Context

Setup Overview is Phase 5 slice #9, the last read-only surface before Login. The current surface is `templates/setup.html` (56 lines) + `portal.py`:

- `GET /setup` (`portal.py:483`) builds four readiness steps, derives `ready_to_launch` and `next_step`, and renders `setup.html`. It reads `?adapter_id=` to select the adapter shown in the `Active Worker adapter` panel.
- The four steps reuse existing helpers: `_control_plane_setup_state(settings, control_status)`, `_effective_budget_settings(...)["confirmed"]`, `_active_adapter_for_request(...)["launchable"]`, and a `project_capability` state of `launch_ready` across `_project_view_model` projections.
- `ready_to_launch = all(step["state"] == "ready" ...)`; `_next_setup_step` (`portal.py:913`) returns `Open task board` → `/projects/{id}/board` when ready, otherwise the first non-ready step's name/href/detail.
- There are **no mutations on this page.** Every card is a link to a Settings destination.

All four destinations are React-owned as of slice #8, which is the gate this slice was ordered behind. The domain rules live in the setup/readiness helpers, so this slice is transport (`react-portal-shell`): a bounded JSON read plus a React view. It is strictly smaller than slices #6–#8 — there is no action to content-negotiate.

## Goals / Non-Goals

**Goals:**
- React owns `/setup` when the complete build exists; Jinja renders it otherwise, same URL.
- A bounded authenticated JSON read reusing the existing readiness builders and `_next_setup_step`.
- Bookmarkable `?adapter_id=` preserved end to end, and forwarded onward to Worker Settings.
- Bounded, allow-listed `active_adapter` projection.
- Setup becomes in-shell React navigation with sidebar highlighting, closing the Setup group's spec gap.

**Non-Goals:**
- No change to readiness rules, step derivation, or next-action computation.
- No new mutation routes; no negotiation; no schema migration.
- No re-litigation of launch-ready-project readiness.
- No Login, Portal Recovery Surface, or `/app` retirement.
- No deletion of `setup.html`.
- No mobile/narrow-screen redesign.

## Decisions

- **Reuse the Settings pattern.** JSON read in `react_shell.py` guarded by `require_portal_auth`; build-aware GET via the shared `_react_index()`. No new mutation routes, and — unlike slices #6–#8 — no `_wants_react_json` negotiation, because the page has no actions.

- **One shared readiness computation, not two.** `_setup_overview_state(request)` in `portal.py` builds the steps, `ready_to_launch`, `next_step`, the active adapter, and budget settings. Both `setup_overview` (Jinja) and the React JSON handoff call it; neither reimplements it. React renders `steps` and `next_step`; it never derives readiness in the browser. This is what keeps the fallback a true parity oracle — a second copy of the step list would drift on the next edit and surface only as React and Jinja disagreeing, which is precisely the failure the build-aware fallback exists to prevent.

- **The build-aware check runs before the readiness computation.** `setup_overview` calls `_react_index()` first and returns the shell immediately when the build is complete. Readiness evaluation touches the database, constructs the Local Runner backend, and evaluates capability per connected project; computing all of it and then discarding it to serve a static index would make every React `/setup` load pay for a Jinja render nobody sees. This also matches the existing Settings routes, which check the index first.

- **`tracking.mode` is the single source for adapter tracking, on both renderers.** `setup.html` previously read `active_adapter.verification_evidence.get('tracking_mode', 'unverified')` while the Worker Settings projection (`react_shell.py`) reads `tracking.mode` off the view model — two paths to one fact. This slice converges both on `tracking.mode`, including updating the Jinja template, rather than leaving React and Jinja reading different sources for the same displayed value. The rendered output is unchanged: `tracking_mode_presentation` (`tracking_modes.py:60-61`) resolves an absent or unrecognized mode to `_UNVERIFIED_PRESENTATION`, whose `mode` is the string `"unverified"`, which is exactly what the old `verification_evidence` default produced. Converging is a smaller and safer end state than documenting the divergence and preserving it.

- **`tracking_mode` is always a string.** Because the view model resolves absent modes to `"unverified"`, the JSON `tracking_mode` field is never `null` in practice. React still renders an explicit unverified state defensively, but the contract does not promise a null and no scenario depends on one.

- **`adapter_id` stays bookmarkable, and the server keeps owning selection.** React reads `?adapter_id=` from the URL and passes it through to the JSON read. `_active_adapter_for_request` still performs the pick, including its existing fallback when the id is absent or unknown. React does not choose the adapter, does not hold it as client-only state, and does not need to validate it — the URL stays copy/pasteable and the selection rule stays in one place.

- **Bounded, allow-listed `active_adapter`.** Only the four fields `setup.html` renders are serialized: `name`, `verification_status`, `launchable`, and `tracking_mode` (from `tracking.mode`). The full `verification_evidence` blob is not exposed. Same discipline as slice #7 stripping the Worker `executable` detection detail and slice #8 deliberately surfacing operator-facing `root_path`: operator-facing configuration in, internal detection detail out.

- **Forward `adapter_id` to Worker Settings.** The Setup Worker card links `/settings/workers`; with `adapter_id` bookmarkable on `/setup`, the link carries `?adapter_id=` so the operator lands on the adapter they were just inspecting. Worker Settings already accepts the parameter — slice #7's defect was exactly this parameter being dropped on redirect, so forwarding it is a one-line fix for a known-real friction, not speculative polish.

- **Setup navigates in-shell.** Once React owns `/setup`, the sidebar Setup link stops being a full-page anchor and becomes client-side navigation, and Setup gains a highlight scenario alongside Sessions and Settings. This is the mechanical consequence of ownership, but it makes this slice the first to touch the `Setup` group clause every prior slice left standing.

- **Readiness drift is already fixed; React copies the corrected rule.** `require-launch-ready-project-setup` (slice #0) corrected the optional-project claim at `portal.py:494`, which now requires a `launch_ready` project for `ready_to_launch`. React consumes the corrected computation. A regression test asserts `ready_to_launch` stays false when no project is launch-ready, so the migration cannot quietly reintroduce the drift the plan called out.

## Risks / Trade-offs

- **Tracking-source convergence touches the fallback template.** Moving `setup.html` onto `tracking.mode` edits a template the migration plan otherwise freezes. It is a same-value refactor, not an extension: the unverified fallback lives in `tracking_mode_presentation` rather than in the template default, so the displayed string is identical. A test asserts the Jinja fallback still renders the tracking value, since the template path is not otherwise exercised once React owns the route.

- **Spec reconciliation touches the Setup group.** The landing requirement's non-migrated scenario and the chrome requirement's full-page-navigation scenario both name Setup. Adding in-shell Setup navigation while those clauses stand would be a direct contradiction, so this slice removes Setup from both lists and adds the Setup highlighting scenario. The project/board active-marking prohibition (`spec.md:372`) is scoped to those routes and stays intact — Setup still must not highlight while a project workspace is open.

- **Pre-existing enumeration drift is noted, not fixed.** Those same two clauses still list Alarms and Settings as full-page/non-migrated even though slices #4 and #6–#8 migrated them. This slice corrects only Setup, the surface it owns. Fixing the rest belongs with the final Jinja retirement change that restates route ownership wholesale; expanding scope here would repeat the enumeration churn the last three slices already paid for.

- **`/app`-based scenarios are untouched.** The chrome highlighting scenarios still specify `/app`, `/app/projects/{id}`, `/app/projects/{id}/board`. Those get restated against canonical URLs when `/app` goes redirect-only in the retirement change; doing it here would spread that work across two changes for no gain.

- **No negotiation means no HTML regression surface.** Because the page has no forms, this slice cannot break an existing HTML caller the way slice #8's shared `archive` route could. The residual risk is the build-aware GET itself, covered by the missing/partial-build fallback tests.
