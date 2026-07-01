## Why

Current estimation accuracy tracking can compare completed Worker actuals to estimates, but the estimator has little reusable calibration signal when a project has too few completed runs. Operators need a deterministic, reviewable way to seed Worker-token calibration cases before enough live history exists, without changing budget semantics or hiding estimates behind opaque multipliers.

## What Changes

- Add a manual estimation calibration catalog for Worker execution token estimates.
- Support a checked-in sample/default catalog for schema examples and regression tests, plus a repo-local `.htb/estimation_calibration.yaml` extension for operator-authored cases.
- Define practical structured calibration cases with task description, project profile, task kind, recommended model, expected token range, optional actual Worker tokens, and rationale.
- Select relevant cases using deterministic filters and simple lexical ranking, then inject a bounded read-only calibration summary into Task Estimation context.
- Preserve a SQL/live-history seam so completed Done-task actuals can later supplement the catalog without replacing the fixture-led first slice.
- Validate checked-in/test catalogs strictly and local operator catalogs leniently with warnings.
- Exclude embeddings/RAG, Portal catalog editor UI, automatic numeric multipliers or clamps, budget semantic changes, and acceptance-quality scoring from this slice.

## Capabilities

### New Capabilities

- `estimation-calibration-catalog`: Manual calibration catalog schema, loading, validation, relevance selection, and bounded estimator context summary for Worker execution token estimates.

### Modified Capabilities

- `estimation-accuracy-tracking`: Estimation accuracy remains Worker execution scoped and gains fixture/catalog-backed regression coverage for estimate bands without changing completed-task dashboard metrics.
- `estimator-project-context`: Project-scoped estimation may include a bounded calibration summary alongside the existing Repo Context Brief, while no-context/global estimation remains supported.

## Impact

- Affected code: estimation calibration loader/validator, estimator prompt payload/context assembly, estimator evals, task-estimation API tests, settings/path resolution for repo-local `.htb` catalog discovery.
- Data/API impact: no database schema migration required for the first slice; SQL/live-history calibration is a preserved seam, not the primary data source.
- Budget semantics: launch budget checks, task `actual_tokens`, and dashboard accuracy remain Worker execution scoped; control-plane estimation/task-breakdown/review spend stays separate.
- Dependencies: no embeddings/vector database/RAG dependency expected.
