## 1. Extract Shared Helper Module

- [x] 1.1 Compare the duplicated helper blocks in all Portal test modules and confirm the shared signatures/defaults to preserve.
- [x] 1.2 Create `tests/portal/helpers.py` with the shared `FakeControlPlaneLLM`, authenticated client helpers, Portal auth headers, Connected Project helper, and project metadata helper.

## 2. Replace Duplicated Helpers

- [x] 2.1 Update each Portal test module to import the shared helpers from `tests.portal.helpers`.
- [x] 2.2 Remove the now-duplicated local helper definitions from the Portal test modules without changing test assertions.
- [x] 2.3 Confirm the extraction did not add `conftest.py`, pytest fixtures, markers, plugins, or pytest configuration.

## 3. Verify

- [x] 3.1 Run `uv run pytest tests/portal -q` and fix any import or parity failures.
- [x] 3.2 Run the repo-required fresh `uv run pytest` after edits.
- [x] 3.3 Run `openspec validate extract-portal-test-harness --strict` before marking the OpenSpec tasks complete.
