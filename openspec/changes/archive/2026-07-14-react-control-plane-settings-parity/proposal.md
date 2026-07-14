## Why

Control Plane Settings is Phase 5 slice #6, the second Settings surface after Budget. It reuses the on-page mutation pattern Budget established but adds the harness's first secret-bearing form (the control-plane API key), a live connection test, and provider→model dropdown coupling. Most of the domain behavior — blank-keeps-key, key-never-displayed, needs_test-after-save, live apply, curated dropdown filtering — is already specified in `control-plane-model-connection`, so this slice is largely transport plus two deliberate additions.

## What Changes

- Make the canonical authenticated `/settings/control-plane` GET build-aware: serve React when the complete frontend build exists, keep the existing Jinja page as missing/partial-build fallback and parity oracle.
- Add a new authenticated, bounded FastAPI JSON read for control-plane state. The projection is **placeholder-only**: it exposes provider, model, base URL, api-key env name, `api_key_present` boolean, estimator/task-breakdown models, legacy-env presence, `shadowed_settings`, curated model list, and sanitized `connection_status` (`online` / `needs_test` / `offline`). The API key value is never serialized in any field.
- Move the curated control-plane model list out of the Jinja template into a single authoritative backend source consumed by the Jinja page, the JSON read, and React (**Decision A**), so the dropdown cannot drift between renderers.
- Give `POST /settings/control-plane` (save) and `POST /settings/control-plane/test` a sanitized, content-negotiated JSON outcome for React/JSON callers while preserving the existing HTML redirects. Bound and sanitize the save `OSError` path so filesystem detail cannot reach the operator.
- Add a React Control Plane Settings view inside the Portal shell on canonical `/settings/control-plane` (no `/app/*` alias): provider/model/base-url/key form with provider-filtered curated dropdown + custom-model path, configured-connection panel, and last-connection-test panel with the three-state status.
- React save/test show inline outcomes and re-fetch authoritative state without leaving the page. The API key input is a password field, empty by default, never prefilled; blank submit keeps the existing key.
- **Dirty-form guard:** the Test button is disabled with an inline "Save before testing" hint whenever the form has unsaved edits, because Test exercises the last-saved-and-applied config, not the in-progress form.

Explicit non-goals (lazy slice boundaries):

- No change to how the key is stored, loaded, or applied; no change to the connection-test call itself.
- No live `GET /v1/models` provider discovery — curated list plus custom-model path only.
- No schema/database migration.
- No migration of Worker or Project Settings, or Setup Overview.
- Do not delete `control_plane.html`; it stays as build-aware fallback until final Jinja retirement.
- Desktop-only.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `control-plane-model-connection`: the curated control-plane model list gains a single authoritative source shared by every renderer, and the Portal exposes an authenticated placeholder-only JSON read of control-plane setup state.
- `react-portal-shell`: React owns the build-aware `/settings/control-plane` surface — a Control Plane Settings view in Portal chrome that consumes the placeholder-only JSON, negotiates the save and test outcomes, disables Test on a dirty form, renders the three-state connection status and env-shadow banner, and re-fetches authoritative state without losing page context.

## Impact

- Backend: `src/foreman_ai_hq/routes/portal.py` (`/settings/control-plane` GET build-aware; save/test negotiated + sanitized envelope; curated list moved to a shared constant), `src/foreman_ai_hq/routes/react_shell.py` (new authenticated control-plane-state JSON endpoint), `src/foreman_ai_hq/templates/control_plane.html` (consume the shared curated list instead of an inline literal).
- Frontend: new `frontend/src/views/ControlPlaneSettings.jsx`, routing in `frontend/src/App.jsx`, shared shell/tokens.
- Preserved: FastAPI remains authoritative for config persistence, secret storage, live apply, and the connection test; `control_plane.html` remains fallback/oracle.
- Tests: `tests/portal/test_react_shell.py` (route selection, JSON auth/shape, placeholder-only invariant, negotiated outcomes, sanitized error), React source/contract assertions for field names and the dirty-form Test guard.
