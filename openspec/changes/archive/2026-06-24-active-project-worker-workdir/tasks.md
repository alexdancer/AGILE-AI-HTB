## 1. Launch Project Root Resolution

- [x] 1.1 Add a small helper that resolves the current Worker launch project root from connected projects, using the most recently updated project for this first slice.
- [x] 1.2 Update board task launch flow to reject normal Worker launch before process creation when no connected project root exists, with error copy linking to `/projects`.
- [x] 1.3 Update Worker Run command/evidence creation to record the selected project root used for launch.

## 2. Worker Adapter Workdir Behavior

- [x] 2.1 Update normal Worker launch planning to prefer the resolved project root over `worker_adapters.workdir`.
- [x] 2.2 Stop auto-configuring OpenCode adapter `workdir` as project setup state when connecting a project, or limit it to legacy compatibility without making it the normal launch source of truth.
- [x] 2.3 Update Worker settings UI/copy so adapter setup is about CLI/auth/models/tracking and does not tell operators to configure a project workdir for normal launches.

## 3. OpenCode Directory Binding

- [x] 3.1 Normalize OpenCode native launch command planning so `opencode run --dir <project_root>` is included for normal launches.
- [x] 3.2 Add regression coverage proving command `cwd` alone is not the only project-boundary evidence for OpenCode launches.

## 4. Tests and Verification

- [x] 4.1 Add tests for launch rejection when no connected project exists.
- [x] 4.2 Add tests for launch using the connected project root even when adapter legacy `workdir` differs.
- [x] 4.3 Add/update portal tests for Worker settings copy/config behavior.
- [x] 4.4 Run targeted launch/portal tests and full `pytest` before marking this change complete.
