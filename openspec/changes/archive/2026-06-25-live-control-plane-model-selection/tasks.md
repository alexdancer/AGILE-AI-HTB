## 1. Config Helpers

- [x] 1.1 Add a small operator-config write helper that updates selected non-secret keys in `.htb/config.toml` while preserving unrelated values.
- [x] 1.2 Add a small secrets helper that ensures a placeholder exists for a configured API key env name in `.htb/secrets.env` without overwriting existing values.
- [x] 1.3 Add tests for config rewrite preservation, placeholder insertion, and existing secret preservation.

## 2. Live Control-Plane Save Route

- [x] 2.1 Add a validated portal payload for provider, model, base URL, API key env name, and the default-checked estimator/breakdown coupling option.
- [x] 2.2 Add `POST /settings/control-plane` to write config first, then replace `app.state.settings` and `app.state.llm_client` for subsequent requests.
- [x] 2.3 Mark `control_plane_model` execution backend status as needs-test/stale after successful saves.
- [x] 2.4 Surface environment override/shadowing when effective runtime values differ from portal-saved config values.

## 3. Portal UI

- [x] 3.1 Replace the read-only control-plane page with a dead-simple form for provider, model, base URL, API key env name, and estimator/breakdown coupling.
- [x] 3.2 Add preset controls for OpenAI `gpt-5.4-mini`, Anthropic `claude-haiku-4-5`, and OpenAI-compatible custom endpoint shape.
- [x] 3.3 Show `needs test` after config changes and keep the existing explicit connection-test action.

## 4. Verification

- [x] 4.1 Add route/UI tests proving a save updates `.htb/config.toml`, hot-swaps the running settings/client, and the next estimation/breakdown request uses the new model.
- [x] 4.2 Add tests proving save failure does not change running settings.
- [x] 4.3 Run targeted tests for settings/operator config/control-plane portal behavior.
- [x] 4.4 Run `pytest`.

## 5. Docs

- [x] 5.1 Update local setup/demo docs to explain live portal changes, no-restart semantics, `.htb/config.toml` persistence, placeholder-only secret handling, and needs-test status.
- [x] 5.2 Ensure docs distinguish Control Plane model settings from Worker Harness model selection.