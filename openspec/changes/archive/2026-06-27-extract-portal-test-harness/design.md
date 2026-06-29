## Context

Portal tests currently duplicate the same setup helpers across the Portal test modules. The duplicated Interface includes fake Control Plane LLM behavior, authenticated Portal clients, Portal auth headers, Connected Project setup, and project task metadata. The production Portal is FastAPI/Jinja with repo-managed `uv run pytest`; this change is intentionally test-only.

## Goals / Non-Goals

**Goals:**
- Concentrate duplicated Portal test setup in one helper Module.
- Preserve existing Portal test assertions and behavior.
- Keep pytest discovery and execution unchanged.
- Make future Portal setup/auth/project-helper changes local to one test helper file.

**Non-Goals:**
- No production Portal route, template, database, Worker Adapter, Control Plane, or AGILE Board behavior changes.
- No new pytest fixtures, `conftest.py`, markers, plugins, or custom pytest configuration.
- No broad test rewrite beyond replacing duplicated helpers with imports.

## Decisions

1. Use `tests/portal/helpers.py` as the single helper Module.
   - Rationale: it is explicit, importable, and does not alter pytest behavior.
   - Alternative rejected: `conftest.py`; it hides dependencies and adds fixture machinery for simple copied functions.

2. Keep the existing helper names and semantics.
   - Rationale: import-only rewrites are the smallest safe diff and preserve test intent.
   - Alternative rejected: renaming helpers or converting them to fixtures; that adds churn without improving the Interface.

3. Keep the helper Module test-only.
   - Rationale: Candidate 1 is an architecture cleanup of the Portal verification surface, not a production behavior change.
   - Alternative rejected: extracting production Portal app factories or auth utilities; no product bug requires it.

4. Verify by running the Portal test suite and then the fresh repo-required test command.
   - Rationale: the Interface is the test surface; unchanged Portal tests are the parity check.

## Risks / Trade-offs

- Import churn across eight test modules could accidentally change a helper default. → Preserve copied helper signatures first, then run `uv run pytest tests/portal -q`.
- A shared helper can hide test coupling if it grows. → Keep only the duplicated setup helpers in scope; do not add convenience wrappers for one-off test logic.
- The capability is internal test infrastructure rather than user-facing behavior. → Spec scenarios focus on preserved verification behavior and explicit non-production impact.
