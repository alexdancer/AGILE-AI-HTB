## Context

Control Plane Settings is Phase 5 slice #6, the second Settings surface after `react-budget-settings-parity`. The current surface is `templates/control_plane.html` + `portal.py`:

- `GET /settings/control-plane` (`portal.py:1224`) renders the provider/model form, configured-connection panel, and last-test panel. The curated model list is a literal in the template (`control_plane.html:9-18`); ~35 lines of vanilla JS (`syncControlPlaneModelControls`) do provider→model filtering.
- `POST /settings/control-plane` (`:1245`) persists non-secret config, writes the key to the ignored `.foreman/secrets.env` (or keeps the existing key when blank), hot-swaps `app.state.settings` + `app.state.llm_client`, and stamps connection status `needs_test`. It already returns a key-free dict to non-HTML callers.
- `POST /settings/control-plane/test` (`:1313`) runs a live `acompletion` against `app.state.llm_client` and records sanitized `online`/`offline` evidence.

The domain capability `control-plane-model-connection` already specifies blank-keeps-key, key-never-displayed, needs-test-after-save, live apply, curated dropdown filtering, custom-model path, and split-model coupling. So this slice is largely transport (`react-portal-shell`) plus two additions the domain cap does not yet cover: a placeholder-only JSON read, and a single authoritative source for the curated list (Decision A).

## Goals / Non-Goals

**Goals:**
- React owns `/settings/control-plane` when the complete build exists; Jinja renders it otherwise, same URL.
- A placeholder-only authenticated JSON read; the key value is never serialized.
- Content-negotiated sanitized save/test outcomes, HTML redirects preserved; fix the save `OSError` leak.
- Curated list in one authoritative backend source consumed by Jinja + JSON + React (Decision A).
- React parity for provider-filtered curated dropdown + custom path, three-state status, env-shadow banner, and the dirty-form Test guard.

**Non-Goals:**
- No change to key storage/load/apply or the connection-test call.
- No live provider model discovery (`GET /v1/models`); curated + custom only.
- No schema migration; no Worker/Project Settings or Setup migration.
- No deletion of `control_plane.html`.
- No mobile/narrow-screen redesign.

## Decisions

- **Reuse the Budget pattern.** JSON read in `react_shell.py` guarded by `require_portal_auth`; negotiate save/test outcomes on the existing `portal.py` routes with `_wants_react_json`; build-aware GET via the shared `_react_index()` (validates referenced assets, so partial build → Jinja). No new mutation routes.
- **Decision A — curated list single source.** Move the `control_plane.html:9-18` literal to a backend constant (e.g. `CURATED_CONTROL_PLANE_MODELS` in the control-plane route module). Jinja reads it via template context; the JSON read serializes it; React consumes it from JSON. This deletes a duplication rather than adding a second React copy — the stale-model-ID risk the project already hit.
- **Placeholder-only read.** The read never carries the key. `api_key_present = bool(os.getenv(env))`, which is `false` for a placeholder-only secrets file because `load_operator_secrets_env` does not export placeholders. This matches the existing "Portal redacts key values" domain scenario.
- **Dirty-form disables Test.** Test exercises `app.state.llm_client`, hot-swapped only at save; it cannot test an unsaved form. React tracks form-dirty state (submitted values vs last-fetched authoritative state) and disables Test with a "Save before testing" hint until the form is pristine. This is the one behavior React adds over Jinja, justified because React holds form state where Jinja's full-reload POST does not.
- **Three-state status, not two.** Save → `needs_test`; failed test → `offline`; passed test → `online`. React renders all three; `needs_test` must never collapse into `offline`.
- **Sanitize the save error.** The current `OSError` branch returns `f"...: {exc}"` (can carry a path). Route it through the bounded/sanitized envelope like the alarm/budget outcomes.

## Risks / Trade-offs

- **Decision A widens the slice past a pure port.** It touches `control_plane.html` and adds a backend constant + JSON field. Accepted: one-time ~15-line refactor that removes a recurring drift bug; deletion beats duplication.
- **Route-ownership enumeration drift.** The landing requirement lists "Settings" as non-migrated; the per-surface ADDED requirement supersedes it for `/settings/control-plane`, same as Budget. Archive-time reconciliation tidies the enumeration when the whole Settings group is React.
- **Dirty-detection fidelity.** Comparing form state to authoritative state must treat the always-empty password field correctly (an empty key field is not a dirty edit). Tests must cover: edit model → Test disabled; save → Test enabled + `needs_test`; blank key on an otherwise-pristine form → not dirty.
- **Env-shadowing.** A save can be silently overridden by an env var; the read exposes `shadowed_settings` and React shows the banner (parity with Jinja `:71`), so the operator is not misled that a shadowed save took effect.
