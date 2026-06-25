# DEMO 2099 Hard Task: Dependency-Aware Task Scheduler CLI

> DEMO DATA ONLY — This task, all examples, and all expected fixtures are synthetic. Use only 2099 dates, DEMO names, `.invalid` email addresses, DEMO addresses, and 999-style fake account numbers. Do not use real customer data. Do not call real external services.

## Purpose

Build a local Python CLI project named `taskrunner`. This is a deliberately large coding task for comparing two execution paths:

1. A coding agent (Claude Code, OpenCode, or Codex) run directly on this task file.
2. The same coding agent launched through AGILE-AI-HTB using the same task file and a separately configured harness Worker budget.

This HARD task should take roughly 15-30+ turns and may push a raw agent toward its context limit. It is the high-end anchor of the comparison set. It tests whether the agent can design a non-trivial DSL parser, implement topological sort and cycle detection from scratch, handle concurrent execution safely, produce deterministic output, and maintain test coverage across multiple modules — all while staying within a token budget that the AGILE-AI-HTB harness would govern. The goal is to show what the harness adds on a long, expensive run: estimate visibility, budget gating, usage authority, launch evidence, alarms or overrides, and review-state evidence — versus a raw agent run that produces only code and a chat transcript, with no budget ceiling and no evidence trail.

## Starting Point for the Worker

Create or update a small local Python project in the working directory. If the directory is empty, create the project. If a minimal scaffold already exists, preserve useful files and implement the missing behavior.

Expected package name:

```text
taskrunner
```

Expected console command:

```text
taskrunner
```

Recommended implementation constraints:

- Use the Python standard library where practical.
- Use `argparse` with subcommands for CLI parsing.
- Use `subprocess` for command execution and `threading`/`concurrent.futures` (or an equivalent stdlib approach) for the concurrency model.
- Use `sqlite3` only for the optional run log.
- Use `re`, `json`, `datetime`, and `pathlib` as needed.
- Do NOT use YAML or TOML for the task format — design the custom `.tasks` line-oriented DSL described below.
- Do not add network dependencies.
- Do not call real external APIs. All example task commands must be local, harmless shell commands like `echo` and `sleep`.
- Add pytest tests. If pytest is unavailable in the scaffold, document the setup and still write tests.
- Do not add auth, billing, deployment, web UI, or cloud integrations.

## Synthetic Data Rules

All sample data and test fixtures must be obviously fake.

Required markers:

- Dates: use year `2099` only.
- Names: include `DEMO`, such as `DEMO Build Ops`.
- Email addresses: use `.invalid`, such as `demo.pipeline.2099@example.invalid`.
- Addresses: include `DEMO`, such as `999 DEMO Pipeline Way, Demo City, ZZ 99999`.
- Account IDs: use `999`-style values, such as `ACCT-999-2099-0001`.
- Task IDs: use `demo-*-2099` style values, such as `demo-build-2099`.

Forbidden:

- Real emails.
- Real addresses.
- Real tokens, secrets, passwords, API keys, or connection strings.
- Commands that send data to real external APIs.
- Task commands that touch the network, delete real files, or have destructive side effects.
- Instructions to publish to any gist, ticket, issue, email, webhook, or cloud object service.

## Product Goal

`taskrunner` reads a task specification file in a custom `.tasks` format, builds a dependency graph, topologically sorts the tasks, and executes them in correct dependency order — running independent tasks in parallel using subprocesses. It detects dependency cycles and reports them, skips dependents of failed tasks, enforces per-task timeouts, and captures per-task output for a final summary.

The tool should be useful enough for a reviewer to run it end-to-end with DEMO fixtures:

```bash
taskrunner validate examples/demo_pipeline_2099.tasks
taskrunner plan examples/demo_pipeline_2099.tasks
taskrunner visualize examples/demo_pipeline_2099.tasks
taskrunner run examples/demo_pipeline_2099.tasks --dry-run
taskrunner run examples/demo_pipeline_2099.tasks --max-parallel 2
taskrunner run examples/demo_pipeline_2099.tasks --task-timeout 30
```

## The `.tasks` DSL

A `.tasks` file is line-oriented. A task block begins with a `:TASK <id>` line and continues with indented `key: value` directive lines until the next `:TASK` line or end of file. Blank lines and lines beginning with `#` (outside a task body) are ignored as comments.

Example fixture `examples/demo_pipeline_2099.tasks`:

```text
:TASK demo-build-2099
  title: Build the demo project
  command: echo "Building..." && sleep 1 && echo "Built"
  tags: [build, demo]

:TASK demo-test-2099
  title: Run demo tests
  command: echo "Testing..." && sleep 0.5 && echo "Tests pass"
  depends_on: [demo-build-2099]
  tags: [test, demo]

:TASK demo-lint-2099
  title: Lint demo code
  command: echo "Linting..." && sleep 0.5 && echo "No issues"
  tags: [quality]

:TASK demo-report-2099
  title: Generate report
  command: echo "Reporting..." && sleep 0.3
  depends_on: [demo-test-2099, demo-lint-2099]
  tags: [report, demo]
```

DSL rules:

- `:TASK <id>` opens a block; `<id>` must be unique and non-empty.
- Recognized directives: `title:`, `command:`, `depends_on:`, `tags:`.
- `command:` is required and is the shell command line to execute.
- `depends_on:` and `tags:` use the inline list form `[a, b, c]`; an empty or absent list is allowed.
- An unknown directive is a validation error that names the directive and task.
- A duplicate `:TASK` id is a validation error.
- A `depends_on` reference to an unknown task id is a validation error.

## Required CLI Commands

The CLI uses `argparse` subcommands.

### `taskrunner validate <file.tasks>`

Parse and validate only; report errors. Exit `0` when valid, non-zero when invalid.

Behavior:

- Parse the DSL and collect every error (missing required fields, duplicate task IDs, unknown directives, unknown dependency references, dependency cycles).
- Report errors deterministically with task IDs and directive names.
- Print a clear success message when the file is valid.

### `taskrunner plan <file.tasks>`

Parse, validate, detect cycles, and print the execution plan.

Behavior:

- Compute a topological ordering of tasks.
- Print the order grouped into "waves" (sets of tasks that can run in parallel because all their dependencies are already satisfied).
- If a cycle exists, print the specific cycle path (for example `demo-a-2099 -> demo-b-2099 -> demo-a-2099`) and exit non-zero — not just "cycle detected".

### `taskrunner run <file.tasks>`

Execute tasks in topological order, running independent tasks in parallel.

Options:

- `--dry-run`: Show what would run, in order, without executing any command (no side effects).
- `--max-parallel <n>`: Limit concurrency; never exceed `<n>` simultaneously running tasks. Default is a sensible small number such as `4`.
- `--task-timeout <seconds>`: Kill a task that exceeds the timeout and mark it `failed`. Default `30`.

Behavior:

- Drive each task through the state machine: `pending -> ready -> running -> done | failed | skipped`.
- A task becomes `ready` when all of its dependencies are `done`.
- Execute `ready` tasks with `subprocess.Popen`, capturing stdout and stderr per task.
- When a task `fails` (non-zero exit or timeout), mark every transitive dependent `skipped`.
- Enforce the concurrency limiter strictly: at no point may more than `--max-parallel` tasks be in the `running` state.
- Print a final summary table: each task's id, final state, duration, and exit code, plus the captured output available per task.
- Exit non-zero if any task ended `failed`.

### `taskrunner visualize <file.tasks>`

Output a Mermaid flowchart of the dependency graph.

Behavior:

- Emit a `flowchart TD` (or `graph TD`) block.
- One node per task (id and title), one edge per `depends_on` relationship pointing from dependency to dependent.
- Output must be deterministic (nodes and edges sorted by task id).

## Architecture Requirements

- **State machine**: explicit task states `pending`, `ready`, `running`, `done`, `failed`, `skipped`, with well-defined transitions.
- **Cycle detection**: detect cycles in the dependency graph and report the actual cycle path, not just a boolean.
- **Parallel execution**: use `subprocess.Popen` with captured output; run independent tasks concurrently up to the concurrency limit.
- **Failure propagation**: when a task fails, mark all transitive dependents `skipped`.
- **Timeouts**: a per-task timeout kills the process and marks the task `failed`.
- **Output capture**: per-task stdout/stderr captured and surfaced in the final summary.
- **Concurrency limiter**: never exceed `--max-parallel` running tasks at any instant.
- **Determinism**: ordering, plan waves, visualize output, and summaries must be deterministic given the same input (sort ties by task id).

## Required Project Files

If creating from scratch, include:

```text
pyproject.toml
README.md
taskrunner/__init__.py
taskrunner/cli.py
taskrunner/parser.py
taskrunner/graph.py
taskrunner/executor.py
taskrunner/visualizer.py
taskrunner/db.py
examples/demo_pipeline_2099.tasks
examples/demo_diamond_2099.tasks
examples/demo_cycle_2099.tasks
tests/test_parser.py
tests/test_graph.py
tests/test_plan.py
tests/test_executor.py
tests/test_visualizer.py
tests/test_integration.py
```

Module responsibilities:

- `cli.py` — argparse subcommands and exit codes.
- `parser.py` — `.tasks` DSL parsing and structural validation.
- `graph.py` — dependency resolution, topological sort, cycle detection with cycle path.
- `executor.py` — parallel execution engine, state machine, timeouts, failure propagation, concurrency limiter.
- `visualizer.py` — Mermaid output.
- `db.py` — optional: log runs to SQLite (used by stretch items; may be a thin stub initially).

You may use a different internal module split if the public CLI behavior and tests are equivalent.

## Testing Requirements

Write at least 18-20 pytest tests covering:

1. Parser: a valid `.tasks` file parses into the expected tasks.
2. Parser: a task missing the required `command:` field is reported.
3. Parser: a duplicate `:TASK` id is reported.
4. Parser: an unknown directive is reported with the directive and task names.
5. Parser: a `depends_on` reference to an unknown task id is reported.
6. Graph: a linear chain of dependencies sorts in order.
7. Graph: diamond dependencies sort with the join task last.
8. Graph: fully independent tasks form a single parallel wave.
9. Graph: cycle detection reports the actual cycle path, not just a flag.
10. Plan: the printed topological ordering / waves are correct for the diamond fixture.
11. Executor: a dependency chain runs sequentially in order.
12. Executor: independent tasks run in parallel.
13. Executor: `--max-parallel` cap is never exceeded (assert peak concurrency).
14. Executor: a failed task causes its dependents to be marked `skipped`.
15. Executor: a task exceeding `--task-timeout` is killed and marked `failed`.
16. Executor: `--dry-run` produces no side effects (no command executes).
17. Executor: per-task output is captured and present in the summary.
18. Visualizer: Mermaid output has the correct nodes and edges for the fixture.
19. Integration: parse + plan + run a 4-task diamond end-to-end with all tasks `done`.
20. Integration: a fixture containing a cycle fails `validate` and `plan` with the cycle path.

## README Requirements

The README should include:

- DEMO-only warning.
- Installation/setup commands.
- The `.tasks` DSL grammar and an annotated example.
- Example commands using the provided fixtures.
- Explanation of the state machine and failure propagation.
- Explanation of the concurrency model and timeouts.
- Statement that the project is local-only and does not call external APIs.

## Acceptance Criteria

The task is complete when:

- `taskrunner --help` works and lists `validate`, `plan`, `run`, and `visualize`.
- `validate` accepts the valid fixtures and rejects the cycle fixture with the cycle path.
- `plan` prints a correct topological ordering / waves for the diamond fixture.
- `run` executes tasks in dependency order, parallel where possible, honoring `--max-parallel`.
- A failed task marks its dependents `skipped`.
- `--task-timeout` kills and marks a long task `failed`.
- `--dry-run` produces no side effects.
- `visualize` emits deterministic Mermaid output.
- Per-task output appears in the final summary.
- Tests pass with `pytest` or the project runner.
- README explains the DSL, state machine, and DEMO-only safety.
- No real data, real secrets, or real external service calls are present.

## Stretch Requirements for Larger Token-Usage Runs

If the core task is completed quickly, continue with these optional items in order. Stop when the run budget or operator instructions require stopping.

1. Implement `db.py` to log each run (run id, started/finished timestamps, per-task states) to SQLite and add `taskrunner history` to list past runs.
2. Add `taskrunner run --only "tag"` and `--skip "tag"` to filter tasks by tag (while preserving dependency correctness).
3. Add `taskrunner run --continue-on-failure` that runs independent branches even after one branch fails.
4. Add `--retries <n>` with per-task retry on failure before marking `failed`.
5. Add golden-file tests for `plan` and `visualize` output.
6. Add a `--json` summary mode for `run` with deterministic per-task results.
7. Add a fixture generator that builds a deterministic 20-task graph (`demo-*-2099`) with mixed chains and diamonds.
8. Add tests for nested/multi-node cycles (3+ tasks in the cycle).
9. Add `taskrunner plan --critical-path` to report the longest dependency chain.
10. Add a short `docs/DEMO_2099_OPERATOR_NOTES.md` describing the local-only demo.

## Worker Instructions

Work like a careful coding agent:

- Inspect the current project before editing.
- Make focused changes.
- Prefer simple, deterministic implementation over cleverness.
- Implement and test one module at a time: parser, then graph, then executor, then visualizer, then integration.
- Keep all example task commands harmless (`echo`, `sleep`) and synthetic.
- Run tests and fix failures.
- Do not commit changes unless explicitly asked.
- Do not call external services.
- Do not use real customer-like examples.
- If blocked, report the exact command and error.

## Expected Final Response From Worker

When finished, summarize:

- files changed;
- commands run;
- test results;
- implemented CLI subcommands;
- the state machine and concurrency model implemented;
- any incomplete stretch items;
- confirmation that all examples are synthetic DEMO 2099 data and all task commands are harmless local commands.
