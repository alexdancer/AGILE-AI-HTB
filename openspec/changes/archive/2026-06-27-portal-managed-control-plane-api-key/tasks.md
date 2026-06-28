## 1. Secret helper behavior

- [x] 1.1 Add a focused helper that writes a non-empty control-plane API key value to `.htb/secrets.env` for the configured env name while preserving unrelated entries.
- [x] 1.2 Ensure blank API key submissions preserve any existing secret value and do not replace it with a placeholder.
- [x] 1.3 Load the saved secret into the current process after a successful save so subsequent control-plane requests can use it without restart.

## 2. Portal settings flow

- [x] 2.1 Extend the control-plane settings payload to accept an optional API key value.
- [x] 2.2 Update `/settings/control-plane` save handling to persist non-secret config first, then write/load the submitted secret only after config save succeeds.
- [x] 2.3 Keep prior connection status marked `needs_test` after saving settings or a new key.

## 3. Portal UI

- [x] 3.1 Add a password-style API key field to the primary control-plane settings form with copy that blank keeps the existing key.
- [x] 3.2 Move API key env-name and base URL mechanics into an advanced/collapsed section while keeping provider/model/key as the normal path.
- [x] 3.3 Continue showing only API-key presence and never render raw key values in page, JSON, or status evidence.

## 4. Verification

- [x] 4.1 Add or update portal tests for saving a new key, preserving an existing key on blank submit, keeping `.htb/config.toml` secret-free, and redacting key values.
- [x] 4.2 Run targeted control-plane portal tests.
- [x] 4.3 Run `openspec validate portal-managed-control-plane-api-key --strict` and `uv run pytest` before marking tasks complete.
