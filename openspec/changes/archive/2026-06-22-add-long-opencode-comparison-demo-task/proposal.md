## Why

AGILE-AI-HTB needs a repeatable, realistic demo task that lets an operator compare normal OpenCode execution against OpenCode launched through the harness and inspect token usage, launch governance, and review evidence. The current demo materials prove local launch and tracking, but they do not provide a deliberately long coding task artifact designed to produce meaningful Worker token usage during side-by-side testing.

## What Changes

- Add a long, standalone synthetic markdown coding task for a small Python CLI project that OpenCode can implement directly or through AGILE-AI-HTB.
- Make the task complicated enough to exercise planning, implementation, tests, debugging, and report/revision behavior without requiring a large production app.
- Include explicit synthetic-data constraints: 2099 dates, DEMO identifiers, `.invalid` emails, 999-style account numbers, and no real external API calls or real customer data.
- Add an operator runbook for comparing:
  - direct OpenCode execution on the task, using OpenCode's native usage output as the baseline; and
  - AGILE-AI-HTB launch of the same task with the OpenCode Worker Adapter and a separately configured harness budget.
- Keep the claim honest: the comparison demonstrates accounting visibility, budget gating, launch/review governance, and measured outcomes. It does not claim automatic token savings when the same full task is sent to OpenCode in both flows.
- Add tests or static checks that prevent the demo task from containing real-looking production data or instructions to call real external services.

## Capabilities

### New Capabilities

- `long-opencode-comparison-demo`: Defines the long synthetic coding task artifact, safety constraints, comparison runbook, and evidence expectations for direct OpenCode versus AGILE-AI-HTB OpenCode Worker execution.

### Modified Capabilities

- `markdown-task-intake`: Clarifies that the long comparison task may be submitted through existing markdown intake without changing file precedence or validation semantics.
- `budgeted-launch-control`: Clarifies that the comparison runbook intentionally uses a different harness Worker budget than the direct OpenCode baseline and should surface launch blocks, overrides, alarms, or review evidence according to existing budget rules.

## Impact

- Docs/demo artifacts: new long markdown coding task under a demo/task location and a short comparison runbook.
- Tests: add a fake-data invariant/static safety test for the new markdown artifact and any generated demo fixtures.
- Existing OpenCode integration: no new adapter family and no generic provider-key flow; the comparison uses the existing OpenCode Worker Adapter identity with `native_usage` or `proxy_governed` tracking when verified.
- Existing app behavior: no breaking API changes expected; any harness execution should use existing markdown intake, budget launch control, Worker Run lifecycle, and review disposition behavior.
