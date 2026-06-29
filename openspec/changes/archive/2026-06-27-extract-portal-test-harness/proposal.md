## Why

Portal tests repeat the same setup Interface across eight modules: fake Control Plane LLMs, authenticated `TestClient` construction, Portal auth headers, Connected Project creation, and project-bound task metadata. This shallow repeated Module makes Portal test changes noisy and easy to drift.

## What Changes

- Add one shared Portal test harness helper Module for the duplicated setup code.
- Update Portal test modules to import the shared helpers instead of carrying local copies.
- Preserve existing Portal test behavior and assertions; this is test architecture cleanup only.
- Avoid new pytest machinery: no `conftest.py`, fixtures, markers, plugins, or discovery changes unless implementation proves a helper-only extraction cannot work.
- No production behavior, Portal routes, templates, database schema, or public APIs change.

## Capabilities

### New Capabilities
- `portal-test-harness`: Shared internal test harness for Portal test setup, covering authenticated clients, fake Control Plane LLM responses, Connected Project setup, and project task metadata helpers.

### Modified Capabilities
- None.

## Impact

- Affected tests: `tests/portal/test_workers.py`, `tests/portal/test_board.py`, `tests/portal/test_sessions.py`, `tests/portal/test_control_plane.py`, `tests/portal/test_alarms.py`, `tests/portal/test_dashboard.py`, `tests/portal/test_auth.py`, and `tests/portal/test_setup.py`.
- New test helper Module: `tests/portal/helpers.py`.
- Verification: `uv run pytest tests/portal -q` and the repo-required fresh `uv run pytest` after edits.
- No runtime dependencies or application code changes.
