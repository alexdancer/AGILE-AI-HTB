## 1. Control-plane model separation

- [x] 1.1 Add explicit control-plane model settings and env names while preserving existing compatibility aliases.
- [x] 1.2 Update app startup/model-client wiring so control-plane calls use the explicit control-plane model configuration.
- [x] 1.3 Add a control-plane connection test path that records sanitized success/failure evidence without launching a Worker Harness.
- [x] 1.4 Update Portal/settings copy so AGILE-AI-HTB model setup is clearly separate from Worker Harness setup.
- [x] 1.5 Add tests for missing, valid, failing, and legacy-alias control-plane model configuration behavior.

## 2. Worker model discovery

- [x] 2.1 Add persistence for discovered Worker Harness models, including adapter id, provider/model id, availability status, and discovery timestamp.
- [x] 2.2 Add adapter interface methods for native model discovery and native usage capability reporting.
- [x] 2.3 Implement OpenCode native diagnostics/model discovery using real CLI commands, with sanitized failure handling.
- [x] 2.4 Show discovered Worker models and discovery status in the Worker adapters Portal page.
- [x] 2.5 Add tests for successful discovery, discovery failure, stale/no discovery, and UI launch-readiness implications.

## 3. Tracking modes and adapter verification

- [x] 3.1 Add tracking-mode fields to adapter verification/session metadata for `proxy_governed`, `native_usage`, and `observed_only`.
- [x] 3.2 Preserve existing proxy-governed verification behavior as one valid tracking mode.
- [x] 3.3 Spike and capture exact OpenCode output for `opencode run --format json`, `opencode stats`, and/or `opencode export` before marking native usage authoritative.
- [x] 3.4 Implement OpenCode native usage verification only after trustworthy usage evidence can be parsed for a launched session.
- [x] 3.5 Block normal governed launch for observed-only adapters while preserving diagnostics/proof-run evidence.
- [x] 3.6 Add tests for proxy-governed, native-usage, and observed-only verification outcomes.

## 4. Governed Worker launch updates

- [x] 4.1 Update launch guardrails to require verified tracking mode and compatible discovered Worker model.
- [x] 4.2 Update task estimation/recommendation flow so Worker model recommendations are constrained by selected adapter discovered models.
- [x] 4.3 Update OpenCode launch command construction to pass selected discovered model in native mode.
- [x] 4.4 Record selected adapter, selected model, tracking mode, and usage source on Worker sessions and task metadata.
- [x] 4.5 Preserve existing read-only and write-capable git guardrails while accepting either proxy-governed or native-usage token evidence.
- [x] 4.6 Add tests for launch blocked by missing model discovery, incompatible model, unverified tracking mode, and successful native/proxy launch paths.

## 5. Budget and ledger category updates

- [x] 5.1 Extend token ledger metadata to classify spend as control-plane, Worker execution, adapter verification, and reporting/summary where applicable.
- [x] 5.2 Record usage source as proxy-governed or native usage import for Worker execution and verification rows.
- [x] 5.3 Update dashboard/session views to show control-plane spend separately from Worker execution and verification overhead.
- [x] 5.4 Update budget launch checks so Worker launch gates against Worker execution budget while still surfacing total spend.
- [x] 5.5 Add tests for category totals, budget gates, override audit, native usage import, and prevention of double-counting.

## 6. Documentation and verification

- [x] 6.1 Update README/demo docs to explain the two model layers: AGILE-AI-HTB control-plane model and Worker Harness models.
- [x] 6.2 Update local setup instructions so users are not told to provide OpenAI-style Worker credentials for native OpenCode mode.
- [x] 6.3 Add or update a local demo script for connecting control-plane model, discovering OpenCode models, verifying tracking, and launching a read-only proof.
- [x] 6.4 Run targeted tests for settings, adapters, model discovery, verification, launch guardrails, budget ledger, and portal routes.
- [x] 6.5 Run the full `pytest` suite and document any remaining blocker separately before marking the change complete.
