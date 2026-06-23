## 1. Demo Task Artifact

- [x] 1.1 Create `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md` with a clear DEMO 2099 banner, synthetic-data warning, target project overview, and operator instructions.
- [x] 1.2 Define the `incident-ledger` Python CLI scope with required commands: `ingest`, `list`, `dedupe`, `score`, `report`, and `export`.
- [x] 1.3 Add detailed implementation requirements for JSONL parsing, markdown incident parsing, SQLite persistence, deterministic duplicate detection, weighted severity scoring, Markdown/JSON reports, README examples, and pytest coverage.
- [x] 1.4 Add acceptance criteria and stretch sections that can scale token usage without turning the task into an unbounded SaaS/product build.
- [x] 1.5 Ensure all sample records in the task use DEMO identifiers, 2099 dates, `.invalid` emails, fake addresses containing DEMO, and 999-style account or incident numbers.

## 2. Comparison Runbook

- [x] 2.1 Create a runbook documenting how to prepare a fresh target repo/directory for the long comparison task.
- [x] 2.2 Document the direct OpenCode baseline command using `opencode run --format json` or the best available machine-readable OpenCode usage mode, and instruct the operator to save the raw output as baseline evidence.
- [x] 2.3 Document the AGILE-AI-HTB path: submit/paste/upload the same markdown task through existing markdown intake, verify/select the OpenCode Worker Adapter, and launch with verified `native_usage` or `proxy_governed` tracking.
- [x] 2.4 Document that the harness Worker budget is intentionally configured separately from the direct OpenCode baseline and that direct baseline usage is external comparison evidence, not harness Worker spend.
- [x] 2.5 Document expected comparison outputs: direct OpenCode token total, harness estimate, launch block or override when over budget, Worker Run evidence, token ledger rows, alarms/overrun if applicable, and Review task-card evidence.

## 3. Fake-Data and Safety Checks

- [x] 3.1 Add `LongOpenCodeComparisonFakeDataInvariantTests` covering the long task artifact, runbook, and any demo fixtures.
- [x] 3.2 Verify the invariant test checks for DEMO/2099/.invalid/999-style markers and fails on real-looking emails, secrets, real account/customer examples, or instructions to call real external services.
- [x] 3.3 Run the new invariant test and any existing demo fake-data invariant tests.

## 4. Documentation Integration

- [x] 4.1 Add a short pointer from the existing demo docs to the long OpenCode comparison task and runbook.
- [x] 4.2 Keep wording honest: same full task through OpenCode and the harness may use similar Worker tokens; the harness comparison demonstrates budget governance, usage authority, launch/review lifecycle, and measured outcomes under a configured budget.
- [x] 4.3 Confirm docs preserve the model-layer split between control-plane/orchestrator model usage and Worker/coding harness model usage.

## 5. Verification

- [x] 5.1 Run `openspec validate add-long-opencode-comparison-demo-task --strict` and fix artifact issues.
- [x] 5.2 Run targeted pytest for the new invariant tests.
- [x] 5.3 Run the full `pytest` suite if targeted tests pass.
