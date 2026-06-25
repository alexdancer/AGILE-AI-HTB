## 1. Persistence and discovery semantics

- [x] 1.1 Add helper logic to read discovered model IDs from existing adapter discovery evidence/config.
- [x] 1.2 Update model discovery persistence so discovery evidence is refreshed without silently expanding an existing curated allowed-model subset.
- [x] 1.3 Add/update tests for first discovery not auto-allowing models and repeat discovery preserving a curated subset.

## 2. Worker Setup allowed-model selection

- [x] 2.1 Add a Worker Setup POST route that accepts selected allowed models for an adapter.
- [x] 2.2 Validate submitted allowed models are present in the adapter's discovered model inventory before saving.
- [x] 2.3 Update `workers.html` to show discovered model checkboxes and save the allowed subset.
- [x] 2.4 Update setup/readiness copy so empty allowed models means setup incomplete.
- [x] 2.5 Add/update route/template tests for saving allowed models and rejecting undiscovered models.

## 3. Estimate, board, and launch enforcement

- [x] 3.1 Keep estimator Worker recommendations constrained to the adapter's allowed model subset.
- [x] 3.2 Update board launch dropdown fallback so adapters with no allowed models do not offer an unapproved recommended-model option.
- [x] 3.3 Ensure launch guardrails reject discovered-but-disallowed model requests before starting a Worker process.
- [x] 3.4 Add/update tests for recommendation constraint, board dropdown options, and disallowed launch rejection.

## 4. Verification

- [x] 4.1 Run targeted tests covering Worker setup, model discovery, estimation, board launch selection, and launch guardrails.
- [x] 4.2 Run `pytest`.
- [x] 4.3 Mark tasks complete only after verification passes.
