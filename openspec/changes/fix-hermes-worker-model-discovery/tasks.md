## 1. Curated Hermes discovery

- [x] 1.1 Add a shared curated Worker model discovery helper that accepts an adapter kind and source label, reusing the existing Claude Code behavior without changing OpenCode native discovery.
- [x] 1.2 Route the Hermes Worker Adapter through curated discovery so `discover_worker_models(..., "hermes")` never builds or runs `hermes models`.
- [x] 1.3 Preserve allowed-model semantics: a previous operator-approved Hermes subset remains only if still curated, and a fresh curated discovery does not auto-approve models.

## 2. Regression coverage

- [x] 2.1 Add a Worker Adapter unit test proving Hermes discovery returns the curated seeded Hermes inventory and does not call the runner.
- [x] 2.2 Add a Worker Adapter unit test proving Hermes curated discovery preserves an approved subset.
- [x] 2.3 Add or update a Worker Setup route test proving `/settings/workers/hermes/discover-models` returns to the Hermes adapter and renders curated Hermes models.

## 3. Verification

- [x] 3.1 Run the targeted Worker Adapter and Worker Setup tests covering discovery.
- [x] 3.2 Run `openspec validate fix-hermes-worker-model-discovery --strict`.
- [x] 3.3 Run the repo-required fresh pytest check or report any unrelated pre-existing worktree blocker separately.
