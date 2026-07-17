## Context

Worker Settings is Phase 5 slice #7, the third Settings surface after `react-budget-settings-parity` and `react-control-plane-settings-parity`. The current surface is `templates/workers.html` + `portal.py`:

- `GET /settings/workers` (`portal.py:1159`) builds adapter view models via `worker_adapter_view_models` (`worker_setup_view.py:14`), selects the active adapter via `active_adapter_for_request` (query param → default → first configured → first), computes a single `worker_setup_next_action`, and renders `workers.html`.
- Five mutations, all guarded by `require_portal_auth`:
  - `POST /settings/workers/{id}/configure` (`:1187`) — set `is_default`. HTML `303` redirect only.
  - `POST /settings/workers/{id}/allowed-models` (`:1203`) — approve a subset of *already-discovered* models (rejects undiscovered ids `422`). HTML `303` redirect only.
  - `POST /settings/workers/{id}/refresh-diagnostics` (`:1223`) — re-detect the CLI binary on PATH. HTML `303` redirect only.
  - `POST /settings/workers/{id}/verify` (`:1478`) — **live** verification against the selected model/tracking mode. Already negotiates JSON, returns `{passed, adapter_id, session_id, reasons, evidence}`.
  - `POST /settings/workers/{id}/discover-models` (`:1521`) — **live** model discovery. Already negotiates JSON, returns `{passed, adapter_id, models, reasons, evidence}`.

The per-adapter view model is rich and already sanitized where it matters: `supported_models` is the operator-approved subset (`allowed_worker_model_ids`), `discovered_models` is the full inventory, `verification_evidence` is passed through `safe_evidence`, and `tracking`/`connection_type` are derived. The domain rules (readiness, tracking modes, discovery, allow-listing, verification) live in `worker-adapter-verification`, `native-worker-model-discovery`, and `guided-worker-setup`. So this slice is transport (`react-portal-shell`): a bounded JSON read, negotiated outcomes for the three redirect-only mutations, and a React view — mirroring the Control Plane slice.

## Goals / Non-Goals

**Goals:**
- React owns `/settings/workers` when the complete build exists; Jinja renders it otherwise, same URL.
- A bounded authenticated JSON read reusing the existing view builders and `safe_evidence` sanitization; no raw exception/path text.
- Content-negotiated sanitized outcomes for `configure`, `allowed-models`, `refresh-diagnostics`; HTML redirects preserved.
- Verify and Discover-models JSON contracts consumed unchanged.
- React parity for adapter selection, the discover→approve workflow (approve gated behind discovery), live actions with inline outcomes, three-signal readiness/next-action, and diagnostics/verification evidence display.

**Non-Goals:**
- No change to adapter storage, discovery, verification, tracking-authority logic, or the two live-action route shapes.
- No new mutation routes; no schema migration.
- No Control Plane / Budget / Project Settings or Setup migration.
- No deletion of `workers.html`.
- No mobile/narrow-screen redesign.

## Decisions

- **Reuse the Budget/Control-Plane pattern.** JSON read in `react_shell.py` guarded by `require_portal_auth`; negotiate the three redirect-only outcomes on the existing `portal.py` routes with `_wants_react_json`; build-aware GET via the shared `_react_index()` (validates referenced assets, so partial build → Jinja). No new mutation routes.
- **Reuse the existing view builders for the read.** The JSON endpoint calls `worker_adapter_view_models`, `active_adapter_for_request`, and `worker_setup_next_action` — the same functions the Jinja page uses — so React never recomputes adapter readiness or tracking rules. This avoids a second projection drifting from Jinja, matching the Control-Plane "single computation" decision.
- **Bounded, sanitized adapter projection.** The endpoint serializes an explicit allow-list of fields per adapter, not the raw DB row. Evidence-bearing fields (`diagnostics`, `verification_evidence`, `verification_diagnostic`) are already `safe_evidence`-processed by the view builder; the endpoint passes them through without re-adding raw text. Absent optionals are `null`.
- **Live actions unchanged; React consumes them.** `verify` and `discover-models` already return bounded negotiated JSON. React posts with `Accept: application/json`, shows the inline `passed`/`reasons` outcome, and refetches the read for authoritative post-action state. No change to those two routes keeps the slice lazy.
- **Discovery gates approval in the UI too.** `allowed-models` server-side rejects undiscovered ids (`422`). React mirrors this: the approve control only offers `discovered_models`, and is disabled/hidden until discovery has run for that adapter. This is parity with the server rule, not a new rule.
- **Adapter selection is client-preserved across refetch.** The read returns the server's `active_adapter_id`, but after an action React refetches and keeps the operator on the adapter they were editing (the server honors `adapter_id` on redirect; React holds it in view state), so a Verify/Discover/approve does not bounce the operator to the default adapter.
- **Sanitize the three redirect-only outcomes.** Like Control Plane's save `OSError` branch, the negotiated JSON error envelope for `configure`/`allowed-models`/`refresh-diagnostics` carries a bounded, sanitized message — no raw path/exception — while HTML callers keep their existing redirect (with the existing `?error=` query for `allowed-models` validation failures).

## Risks / Trade-offs

- **Larger surface than prior Settings slices.** Five mutations and two live actions vs Control Plane's two. Accepted: the two live actions are consumed unchanged (zero new backend contract), and the three redirect-only mutations get the same negotiation helper Budget/Control-Plane already established, so the incremental backend work is one JSON read plus three small negotiation branches.
- **Route-ownership enumeration drift.** The landing requirement lists "Settings" as non-migrated; the per-surface ADDED requirement supersedes it for `/settings/workers`, same as Budget and Control Plane. Archive-time reconciliation tidies the enumeration when the whole Settings group is React.
- **Evidence sanitization must not regress.** The read must never widen what `safe_evidence` already bounds. Tests assert no raw path/exception text and that only the allow-listed fields appear, mirroring the Control-Plane key-never-present invariant.
- **Live-action latency in the browser.** Verify/Discover can be slow (real CLI/proxy calls). React shows a busy state and disables the action while in flight; it does not add polling or optimistic state — the authoritative read after completion is the source of truth.
