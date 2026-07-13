## 1. Focused Readiness Coverage

- [x] 1.1 Add failing Setup Overview tests proving no Connected Project cannot report launch-ready after Control Plane, budget, and Worker Adapter setup pass.
- [x] 1.2 Add failing tests using a controlled backend fake for defensive `analysis_ready` projection, a real invalid-path project for reachable `blocked` behavior, and preserve earlier blocker priority.
- [x] 1.3 Add a failing test proving a launch-ready project enables readiness and the primary action links to that exact project board even when an earlier project is not launch-ready.
- [x] 1.4 Add a failing test proving a persisted `launch_ready` capability cannot enable readiness when Local Runner is disabled or unavailable.

## 2. Truthful Setup State

- [x] 2.1 Require an available Local Execution Backend before reusing live capability-aware Connected Project view models in `setup_overview`; never accept persisted `launch_ready` capability when the backend is unavailable.
- [x] 2.2 Derive the deterministic launch-ready project candidate, require all four setup steps for overall readiness, and make Project Settings the next action when no project is currently launch-ready.
- [x] 2.3 Link completed setup directly to the selected launch-ready project board and update server-rendered Setup copy only where needed to remove optional-project wording.

## 3. Verification

- [x] 3.1 Run focused Setup/Project Portal tests and confirm all new readiness scenarios pass without real Worker CLI calls.
- [x] 3.2 Run `uv run pytest -q`, `openspec validate require-launch-ready-project-setup --strict`, `openspec validate --specs --strict`, and `git diff --check`.
- [x] 3.3 Perform independent review for contract fidelity, capability reuse, blocker priority, and unintended scope expansion; remediate any blocking findings and rerun affected checks.
