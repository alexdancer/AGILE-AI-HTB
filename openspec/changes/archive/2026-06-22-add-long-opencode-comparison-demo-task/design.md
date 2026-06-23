## Context

The project already supports markdown task intake, budgeted Worker launch control, OpenCode as a first-class Worker Adapter, and budget-authoritative `native_usage` tracking when OpenCode emits trustworthy machine-readable usage. Existing demo materials prove local setup and adapter launch, but they do not provide one deliberately long coding task that can be run both directly with OpenCode and through AGILE-AI-HTB for an operator-visible comparison.

The comparison should not imply that routing the same full prompt through `native_usage` automatically reduces tokens. Direct OpenCode and harness-launched OpenCode may use similar Worker tokens when given the same task. The harness value in this demo is that the operator can configure a different Worker budget, see estimation and launch gating, import usage into the ledger, and review the run with task/session evidence.

Model responsibilities remain separate:

```text
Control-plane/orchestrator model
  estimates, recommendations, task metadata, summaries/reports

Worker/coding harness model
  selected inside OpenCode and launched by the OpenCode Worker Adapter

Tracking mode
  native_usage or proxy_governed determines usage authority, not adapter identity
```

## Goals / Non-Goals

**Goals:**

- Provide a long, realistic synthetic markdown coding task for a small Python CLI project.
- Make the task complex enough to exercise planning, implementation, testing, debugging, and report/revision work.
- Keep the task bounded: one CLI project, local files only, no production APIs, no network dependency.
- Provide an operator runbook for comparing direct OpenCode usage with AGILE-AI-HTB-launched OpenCode usage under a separately configured harness budget.
- Ensure all demo data is obviously synthetic and statically checked.
- Preserve existing markdown intake, Worker Adapter, tracking-mode, budget, and review lifecycle semantics.

**Non-Goals:**

- Do not build a new Worker Adapter or generic provider-key path.
- Do not claim automatic token savings when the same full prompt is sent to OpenCode in both flows.
- Do not require a 750,000-token markdown file; the target is overall task/run complexity and measured usage, not file size.
- Do not add real external services, real customer data, real GitHub/Gist calls, billing, auth, or deployment to the demo task.
- Do not auto-kill native OpenCode mid-run solely because it crosses a budget; existing overrun/review behavior applies unless a proxy-governed/runtime-throttled path is used.

## Decisions

### Decision: Use a standalone synthetic incident-ledger CLI task

Create a markdown task artifact, tentatively `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md`, that asks the Worker to build a Python CLI named `incident-ledger`.

The task should include:

- commands: `ingest`, `list`, `dedupe`, `score`, `report`, and `export`;
- JSONL and markdown incident input formats;
- SQLite persistence and a simple migration path;
- deterministic duplicate detection without extra fuzzy-match dependencies;
- weighted severity scoring;
- Markdown and JSON report output;
- pytest unit and CLI integration tests;
- README/usage examples;
- synthetic fixtures only.

Rationale: this is complex enough to create real Worker token usage but still small enough for OpenCode to complete in a local demo. Alternatives rejected: a giant context-only file, because that mostly tests context ingestion; and a full SaaS app, because it risks failing for unrelated scope, UI, deployment, and dependency reasons.

### Decision: Add a comparison runbook instead of app-specific comparison code

Create a short runbook that tells the operator how to:

1. prepare a fresh demo target repo or directory;
2. run the task directly with `opencode run --format json` and capture native token evidence;
3. submit or paste the same markdown task through AGILE-AI-HTB markdown intake;
4. configure OpenCode Worker Adapter tracking as `native_usage` or `proxy_governed` if available;
5. set a harness Worker budget that is intentionally different from the direct OpenCode baseline;
6. launch or observe the expected budget block/override/review behavior;
7. compare direct OpenCode usage with AGILE-AI-HTB session/ledger evidence.

Rationale: the current product already has the mechanisms needed for the comparison. The missing piece is a repeatable artifact and operator script, not a new runtime subsystem.

### Decision: Treat direct OpenCode usage as external baseline evidence

Direct OpenCode runs are outside AGILE-AI-HTB's budget ledger. The runbook should preserve their usage as a baseline artifact, for example a saved JSON log, but the harness should not import that baseline as Worker execution spend unless a later explicit import feature is proposed.

Rationale: this keeps the accounting story clean. AGILE-AI-HTB governs harness-launched Worker Runs; direct OpenCode is the uncontrolled comparison.

### Decision: Use static fake-data invariant tests

Add a test class named `LongOpenCodeComparisonFakeDataInvariantTests` that scans the task/runbook/demo fixture paths for:

- a DEMO banner;
- 2099 dates;
- `.invalid` emails where emails appear;
- `DEMO` in names/addresses/IDs;
- no real external API instructions;
- no realistic secrets or real-looking customer/account examples.

Rationale: large demo artifacts are easy places to accidentally paste real-looking values. The project has an existing durable demo-data invariant standard, so this change should follow it.

## Risks / Trade-offs

- **Risk: Direct OpenCode token usage may not reach the desired ~750k total on the first try.** → Mitigate by making the task easy to scale: add optional stretch sections for more fixtures, migrations, golden reports, and additional edge cases without changing the core project.
- **Risk: The demo overclaims savings.** → Mitigate with explicit runbook language: same Worker plus same full task may use similar tokens; the harness comparison demonstrates budget governance, accounting, and review under a configured budget.
- **Risk: The task becomes too large to complete reliably.** → Mitigate by keeping the target project local, dependency-light, and CLI-based, with optional stretch requirements clearly separated from must-have acceptance criteria.
- **Risk: Native OpenCode usage evidence shape changes.** → Mitigate by relying on existing OpenCode Worker Adapter verification and documenting that `observed_only` is diagnostic only, not a governed board launch.
- **Risk: Demo fixture data looks real.** → Mitigate with fake-data invariant tests and explicit synthetic constraints in the task artifact.
