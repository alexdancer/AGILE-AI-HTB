## Context

The control-plane model connection already has provider/model/base URL editing, Anthropic support, `.htb/config.toml` persistence, `.htb/secrets.env` placeholders, live runtime hot-swap, and a connection test. The remaining user pain is that the common path still asks operators to understand environment-variable names or manually edit `.htb/secrets.env` before Anthropic/OpenAI works.

This change is local-operator setup only. It does not change Worker Adapter credentials, Worker model selection, proxy governance, or provider clients.

## Goals / Non-Goals

**Goals:**

- Let an authenticated local operator paste a control-plane API key in the portal.
- Store that key in ignored `.htb/secrets.env`, not `.htb/config.toml`.
- Keep provider/model/base URL save behavior and live hot-swap unchanged.
- Make the default UI provider/model/key oriented, with env-name mechanics hidden as advanced.
- Preserve existing secrets when the password field is left blank.
- Keep connection testing explicit and secret-redacted.

**Non-Goals:**

- No external secret vault, OAuth flow, encryption layer, or account management.
- No provider model catalog/discovery.
- No Worker Adapter auth changes.
- No secret display/readback after save.

## Decisions

### Store portal-submitted keys in `.htb/secrets.env`

Use the existing ignored local secrets file rather than adding a dependency or new secret store. The portal writes only the selected control-plane secret value for the configured env-name. `.htb/config.toml` continues to hold only non-secret settings.

Alternative considered: keep placeholder-only secrets and print instructions. Rejected because the user explicitly wants no manual env-variable setup for the normal path.

### Keep env-name as advanced internal configuration

Normal users should see provider, model, optional base URL, and API key. The env-name remains available under advanced settings for compatibility and for operators who already have process-managed secrets.

Alternative considered: remove env-name support entirely. Rejected because current settings, tests, and env override behavior depend on it and it is useful for non-local deployment.

### Blank API key preserves existing secret

A password field cannot safely show the current secret. A blank submit means “keep existing key”; a non-blank submit replaces the stored value for the configured control-plane key env-name.

Alternative considered: always overwrite on save. Rejected because accidental blank submissions would break a working setup.

### Save and test stay separate

Saving writes config/secrets and marks connection status `needs_test`; testing makes the provider call. This avoids turning a temporary network/provider failure into a failed settings save.

Alternative considered: auto-test on save. Rejected as more surprising and harder to recover from.

## Risks / Trade-offs

- Portal can now write a local secret file → Limit scope to authenticated local operator flow, keep `.htb/` ignored, and never echo secret values.
- Environment overrides can still shadow portal-saved values → Preserve existing shadowed-setting warning.
- `.htb/secrets.env` is plaintext → Accept for local developer setup; defer vault/encryption until there is a real multi-user/hosted requirement.
