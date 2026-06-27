## Why

Session evidence surfaces are audit-complete but too noisy for normal review: the sessions list and session report header can expose full task/report text while scrolling. Operators need compact summaries first, with full raw evidence still available on demand.

## What Changes

- Make the sessions index default to compact session/task summaries instead of full task descriptions.
- Make session report headers and evidence summary cards show bounded readable text by default.
- Keep full task text, raw repo context brief text, long launch targets, timeline detail summaries, stdout/stderr-style diagnostics, and other raw evidence available behind native `<details>` or bounded scroll regions.
- Reuse server-rendered Jinja and shared CSS utilities; do not add a frontend framework, schema migration, or JavaScript accordion.
- Preserve auditability: this is a readability change, not evidence deletion.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `portal-evidence-readability`: Session list and session report pages must render compact summaries by default while preserving full evidence behind disclosure or bounded raw sections.
- `portal-quality-system`: Add shared compact-text/readability utility behavior for touched server-rendered Portal templates without a frontend build step.

## Impact

- Affected templates: `src/agile_ai_htb/templates/sessions.html`, `src/agile_ai_htb/templates/session_report.html`, and shared styles in `src/agile_ai_htb/templates/base.html`.
- Affected route context may include small summary fields from `src/agile_ai_htb/routes/portal.py` only if templates cannot safely derive concise display text.
- Affected tests: rendered Portal/session report tests under `tests/api/` or equivalent template coverage.
- No database schema, Worker Adapter behavior, token accounting, model/provider routing, or external dependencies are expected to change.
