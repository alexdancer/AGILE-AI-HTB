# DEMO 2099 Runbook: Direct OpenCode vs AGILE-AI-HTB OpenCode Comparison

> DEMO DATA ONLY — This runbook uses the synthetic task at `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md`. Do not paste real customer data, real secrets, real tokens, real addresses, or real service endpoints into the demo target repo.

Synthetic examples in the task use `.invalid` email addresses such as `demo.dispatch.2099@example.invalid`, DEMO addresses, 2099 dates, and 999-style fake account IDs.

## What This Comparison Proves

This runbook compares the same long coding task through two paths:

```text
Same synthetic task markdown
        │
        ├─ Direct OpenCode
        │    └─ outside AGILE-AI-HTB governance
        │    └─ native usage output is baseline evidence
        │
        └─ AGILE-AI-HTB + OpenCode Worker Adapter
             └─ harness estimate / launch guardrails / budget policy
             └─ Worker Run evidence / token ledger / review state
```

The honest claim:

- Direct OpenCode shows uncontrolled baseline token usage for the task.
- AGILE-AI-HTB shows operator governance around the Worker run: estimate, budget gate, override acknowledgement, launch evidence, usage import, alarms, and review evidence.
- If both paths send the same full task to the same OpenCode model, Worker token usage may be similar. The harness does not automatically compress the prompt in `native_usage` mode.

## Model and Tracking Responsibilities

Keep these layers separate:

```text
Control-plane/orchestrator model
  Used by AGILE-AI-HTB for estimation, recommendations, summaries, reports.

Worker/coding harness model
  Selected and run by OpenCode for the actual coding task.

Worker Adapter identity
  OpenCode local CLI integration.

Tracking mode
  proxy_governed  -> Worker requests pass through Harness Proxy when configured.
  native_usage    -> OpenCode uses native auth; harness imports trustworthy usage after the run.
  observed_only   -> diagnostic only; not a normal governed board launch.
```

## Files Used

```text
demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md
docs/DEMO_2099_OPENCODE_COMPARISON_RUNBOOK.md
```

## 0. Verify Local Tooling

From this repo:

```bash
cd /Users/alex/Documents/Fired-Fest-Token-Traker-Harness/AI-Harness-Token-Tracker
opencode --version
opencode run --help
```

Expected:

- `opencode` is installed.
- `opencode run` supports `--format json` and `--file`.

If OpenCode is not installed or authenticated, stop and fix OpenCode first. Do not substitute fake usage numbers.

## 1. Prepare Two Fresh Target Directories

Use separate directories so the direct run and harness run do not contaminate each other.

```bash
mkdir -p .demo/opencode-comparison/direct-target
mkdir -p .demo/opencode-comparison/harness-target
mkdir -p .demo/opencode-comparison/evidence
```

Each target should start empty or contain only a minimal Python scaffold. The task file tells the Worker what to create.

## 2. Direct OpenCode Baseline

Run OpenCode directly against the task file and save raw JSON event output.

```bash
cd /Users/alex/Documents/Fired-Fest-Token-Traker-Harness/AI-Harness-Token-Tracker

mkdir -p .demo/opencode-comparison/direct-target .demo/opencode-comparison/evidence
cp demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md .demo/opencode-comparison/direct-target/task.md

opencode run \
  --dir .demo/opencode-comparison/direct-target \
  --model openai/gpt-5.5 \
  --variant high \
  --format json \
  "$(printf 'Implement this DEMO 2099 incident-ledger task. Work until the required acceptance criteria pass, then summarize files changed and verification commands.\n\n'; cat .demo/opencode-comparison/direct-target/task.md)" \
  | tee .demo/opencode-comparison/evidence/direct-opencode-raw-events.jsonl
```

Notes:

- The direct run is outside AGILE-AI-HTB budget governance.
- Save the full raw event stream. It is the baseline evidence.
- Use OpenCode's selected model/auth exactly as you normally would for the baseline.
- Do not paste real API keys into prompts or logs.

After the run, inspect the saved events for token usage fields emitted by your OpenCode version. The exact event names may vary by OpenCode release, but the evidence should remain machine-readable.

## 3. Start AGILE-AI-HTB with operator setup

Use the operator setup path. If you need an isolated comparison database, edit `.htb/config.toml` after init and set `database_path = ".demo/opencode-comparison/harness.db"` before starting the portal.

```bash
uv run htb init

# Required: edit .htb/secrets.env once.
# AGILE_AI_HTB_CONTROL_API_KEY is the portal/control-plane estimator key, not the OpenCode Worker auth.

uv run htb serve
```

In another terminal:

```bash
export BASE_URL="http://127.0.0.1:8000"
set -a
source .htb/secrets.env
set +a

uv run htb check
curl -fsS "$BASE_URL/health"
curl -fsS -X POST "$BASE_URL/settings/control-plane/test" \
  -H "Authorization: Bearer $TOKEN_TRACKER_PORTAL_TOKEN" \
  -H "Accept: application/json"
```

Expected:

```text
{"status":"ok"}
..."passed":true...
```

If the control-plane test says `missing control-plane API key env: AGILE_AI_HTB_CONTROL_API_KEY`, edit `.htb/secrets.env` with the control-plane API key and restart `htb serve` before uploading the markdown task. Otherwise the board will create a `Blocked` task with `Estimator unavailable or invalid; manual estimate required.`

## 4. Verify or Configure the OpenCode Worker Adapter

Use the Portal first:

```text
http://127.0.0.1:8000/login
```

Log in with the portal token generated by `htb init` in `.htb/secrets.env`:

```text
TOKEN_TRACKER_PORTAL_TOKEN=<generated-portal-token>
```

Then check:

```text
/settings/workers
```

Configure OpenCode with:

- adapter identity: OpenCode
- workdir: absolute path to `.demo/opencode-comparison/harness-target`
- model: the OpenCode model you intend to use
- tracking mode: verified `native_usage` or `proxy_governed`

The harness OpenCode command must bind that workdir through OpenCode's native project-dir flag, not only the subprocess cwd:

```text
opencode run --dir /absolute/path/to/.demo/opencode-comparison/harness-target --model <worker-model> --format json <prompt>
```

If OpenCode reports writes under a repo-level path such as `incident-ledger/` while `.demo/opencode-comparison/harness-target` remains empty, treat the run as a retryable workdir mismatch. Do not count repo-level `incident-ledger/` output as successful harness evidence.

Important:

- `native_usage` may launch without Harness Proxy credentials only when verification proves machine-readable, selected-model-aware, token-complete, successful-exit, run-bound usage evidence.
- `proxy_governed` requires Harness Proxy URL/session API key wiring and provides runtime request governance.
- `observed_only` is for diagnostics and must not be treated as a normal governed board launch.

## 5. Submit the Same Markdown Task Through AGILE-AI-HTB

Use the board markdown intake path:

```text
/board
```

Submit either:

- upload `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md`; or
- paste the full markdown content into the estimator.

Expected:

- the portal creates a Task Breakdown Review first, with no AGILE Board task cards before acceptance;
- accepted candidate(s) are sent to estimation and preserve markdown-source context;
- Task Breakdown Agent usage is tracked as `task_breakdown` orchestration spend, estimation usage is tracked as `estimation`, and both remain separate from Worker execution spend.

## 6. Configure a Different Harness Worker Budget

The comparison is meaningful because the harness budget is explicit and separately configured. Pick a Worker budget below or near the direct baseline if you want to demonstrate blocking or override behavior.

Examples:

```text
Direct OpenCode baseline: external evidence only
Harness Worker budget: configured lower than the direct baseline to show gate/override/review behavior
```

For `native_usage`, if the estimate exceeds remaining Worker budget, launch should require explicit acknowledgement that native OpenCode requests cannot be throttled mid-run. The run may finish and then reconcile usage afterward.

## 7. Launch Through AGILE-AI-HTB

From the board:

1. Select the long markdown task.
2. Confirm the selected Worker Adapter is OpenCode.
3. Confirm the tracking label is one of:
   - `Tracked via Native Usage`; or
   - `Governed via Harness Proxy`.
4. Confirm the recommended model is supported by the adapter.
5. Launch normally if the estimate fits the configured Worker budget.
6. If the estimate exceeds budget, use the explicit override flow only if you intend to demonstrate over-budget launch behavior.

Expected harness evidence:

- task estimate;
- launch-ready adapter metadata;
- budget gate result;
- `budget_override=true` if an override was approved;
- Worker Run/session ID;
- stdout/stderr/exit evidence;
- native or proxy usage evidence;
- effective project-root/workdir evidence showing files in `.demo/opencode-comparison/harness-target`;
- no suspicious outside-workdir paths such as repo-level `incident-ledger/` being counted as the harness target;
- token ledger rows for harness Worker execution;
- alarms or overrun evidence when thresholds are crossed;
- Review or Done task-card state after completion.

## 8. Compare the Results

Create a small comparison note in the evidence directory:

```text
.demo/opencode-comparison/evidence/DEMO_2099_COMPARISON_NOTES.md
```

Suggested table:

| Field | Direct OpenCode | AGILE-AI-HTB OpenCode |
|---|---:|---:|
| Task file | DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md | DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md |
| Target directory | direct-target | harness-target |
| Worker model | record selected model | record selected model |
| Prompt/input tokens | from OpenCode JSON | from harness usage evidence |
| Completion/output tokens | from OpenCode JSON | from harness usage evidence |
| Total tokens | from OpenCode JSON | from token ledger/session report |
| Budget configured | none / external | explicit Worker budget |
| Launch blocked? | not applicable | yes/no |
| Override approved? | not applicable | yes/no |
| Alarm generated? | not applicable | yes/no |
| Final task state | external | Done or Review |

## 9. What to Say in the Demo

Use this framing:

```text
Direct OpenCode tells us what a normal uncontrolled run spent.
AGILE-AI-HTB gives the operator a governed path: estimate first, budget gate before launch, explicit override when needed, authoritative usage evidence when available, ledger entries, alarms, and review state.
```

Avoid this framing:

```text
The harness automatically makes OpenCode use fewer tokens on the same full prompt.
```

That is not true for normal `native_usage` execution.

## 10. Cleanup

This demo only writes local synthetic files under `.demo/opencode-comparison` unless the operator chooses a different target directory.

```bash
rm -rf .demo/opencode-comparison/direct-target
rm -rf .demo/opencode-comparison/harness-target
```

Keep `evidence/` if you want to preserve comparison notes and raw OpenCode output.
