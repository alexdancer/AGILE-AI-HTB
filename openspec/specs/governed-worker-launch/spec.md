# governed-worker-launch Specification

## Purpose
Define how the harness launches local Worker Sessions under governance, including read-only proof runs, write-capable git guardrails, model selection, verification, commits, optional pull requests, and failure evidence preservation.

## Requirements

### Requirement: Read-only launch proof
The system SHALL support a first read-only Worker Session that inspects the connected repository and produces a session report artifact without modifying repository files, using either proxy-governed or native-usage tracking mode, and proxy-governed mode SHALL forward upstream through direct provider clients rather than LiteLLM.

#### Scenario: Read-only session succeeds through proxy-governed tracking
- **WHEN** OpenCode runs the read-only repo inspection task through the Harness Proxy
- **THEN** the system records Worker token usage from the direct upstream provider response, saves a session report artifact with language, test command, and top-level structure, and leaves the repository without file changes

#### Scenario: Read-only session succeeds through native usage tracking
- **WHEN** OpenCode runs the read-only repo inspection task through native harness configuration and the Local Runner imports trustworthy usage evidence
- **THEN** the system records Worker token usage from native usage evidence, saves a session report artifact, records the tracking mode, and leaves the repository without file changes

#### Scenario: Read-only session modifies files
- **WHEN** a read-only Worker Session produces a git diff or file modification
- **THEN** the system marks the session Blocked and preserves logs, token usage, and diff evidence

### Requirement: Write sessions require clean git state
The system SHALL require a detected git repository, visible current branch, and clean working tree before launching write-capable Worker Sessions.

#### Scenario: Dirty repo blocks write task
- **WHEN** the User attempts to launch a write-capable task and the working tree has uncommitted changes
- **THEN** the system blocks launch and shows the cleanliness failure reason

### Requirement: Task branch creation
The system SHALL create a task branch before launching a write-capable Worker Session.

#### Scenario: Task branch created
- **WHEN** a write-capable task passes Launch Guardrails
- **THEN** the runner creates a branch named with the task identity, such as `htb/task-123-short-title`, and launches the Worker on that branch

### Requirement: Harness-owned commit
The system SHALL own final git commits for write-capable Worker Sessions after verification passes.

#### Scenario: Verification passes and Harness commits
- **WHEN** the Worker produces changes, the configured test command passes, and the Harness generates a diff review summary
- **THEN** the Harness creates a commit on the task branch with task/session metadata

#### Scenario: Missing test command requires manual approval
- **WHEN** the Worker produces changes but the Project Profile has no configured test command
- **THEN** the system marks verification as missing test command and requires manual approval before committing

### Requirement: Optional pull request creation
The system SHALL make pull request creation optional after a Harness-owned commit exists.

#### Scenario: GitHub PR option available
- **WHEN** a GitHub remote exists and authenticated `gh` CLI is available
- **THEN** the Portal may offer an Open PR action after the Harness-owned commit

### Requirement: Blocked failure preservation
The system SHALL preserve evidence when Worker execution cannot complete successfully. Retryable Worker Run failures for tasks that were launchable before the attempt SHALL fail the Worker Run and preserve sanitized evidence without moving the task to the Blocked lifecycle state. Hard safety failures, workflow/dependency blockers, read-only project mutation, write-capable verification failure, budget preflight denial without override, and non-launchable preconditions SHALL remain blocking states.

#### Scenario: Worker run fails recoverably
- **WHEN** OpenCode crashes, exits non-zero, times out, or produces no budget-authoritative token usage for the selected tracking mode after an Estimated task has been claimed for launch
- **THEN** the system marks the Worker Run and Worker session failed
- **AND** the task returns to Estimated
- **AND** the system preserves logs, launch return code, sanitized stderr/stdout, tracking mode, branch name when present, and token ledger entries when present
- **AND** the task remains eligible for a later launch retry

#### Scenario: Safety failure remains blocked
- **WHEN** a Worker launch violates a hard safety guardrail such as read-only project mutation or write-capable verification failure
- **THEN** the Task moves to Blocked and the system preserves logs, token ledger entries when present, failure reason, tracking mode, branch name, and any uncommitted diff without automatic retry

### Requirement: Worker launch model selection
The system SHALL launch Worker Sessions with a model selected from the verified adapter's operator-approved allowed model subset. A model that is discovered but not allowed SHALL NOT be launchable from the normal AGILE Board.

#### Scenario: User selects allowed Worker model
- **WHEN** the User launches a task with a model allowed for the selected verified Worker Adapter
- **THEN** the Local Runner passes that model to the Worker Harness launch command and records it on the Worker session

#### Scenario: Selected model is unavailable
- **WHEN** the selected model is not in the selected adapter's allowed model subset
- **THEN** the system blocks launch and shows the model compatibility reason

#### Scenario: Discovered but disallowed model is rejected
- **WHEN** a Worker Adapter has discovered model `opencode/experimental-large`
- **AND** the operator has not included it in the allowed model subset
- **AND** a launch request names `opencode/experimental-large`
- **THEN** the system rejects the launch before starting any Worker Adapter process

### Requirement: Worker Adapter tracking modes govern launchability
The system SHALL treat Worker Adapters as local coding-agent CLI integrations and SHALL separately verify how token usage is proven for each adapter launch.

#### Scenario: Proxy-governed adapter is launchable with proxy evidence
- **WHEN** a Worker Adapter has `proxy_governed` tracking mode
- **AND** Harness Proxy token rows have been verified for the selected model
- **AND** Harness Proxy URL and session API key wiring are present
- **THEN** the adapter is eligible for governed AGILE Board launch if all other Launch Guardrails pass

#### Scenario: Native usage adapter is launchable without proxy wiring
- **WHEN** a Worker Adapter has `native_usage` tracking mode
- **AND** trustworthy native usage evidence has been verified for the selected model
- **THEN** the adapter is eligible for governed AGILE Board launch without requiring Harness Proxy URL or session API key wiring

#### Scenario: Observed-only adapter is not board-launchable
- **WHEN** a Worker Adapter has `observed_only` tracking mode
- **THEN** the normal AGILE Board SHALL NOT launch it for a Task

### Requirement: Native usage is accounting-governed but not runtime request-governed
The system SHALL distinguish native usage accounting authority from proxy runtime request governance.

#### Scenario: Native usage launch does not claim request governance
- **WHEN** a Worker Run uses `native_usage` tracking mode
- **THEN** the system records it as budget-authoritative only through launch/review governance, preflight budget checks, post-run reconciliation, evidence review, and alarms after usage is known
- **AND** the system SHALL NOT label the run as runtime request-governed

#### Scenario: Proxy-governed launch supports runtime request guardrails
- **WHEN** a Worker Run uses `proxy_governed` tracking mode
- **THEN** runtime request guardrails may apply while Worker model calls pass through the Harness Proxy

### Requirement: Native usage budget override acknowledgement
The system SHALL require explicit native-usage acknowledgement when a budget override is used for a native usage launch.

#### Scenario: Native usage override records acknowledgement
- **WHEN** a Task estimate exceeds the remaining daily Worker budget
- **AND** the selected Worker Adapter uses `native_usage` tracking mode
- **AND** the operator chooses Launch with budget override
- **THEN** the operator must acknowledge that native usage cannot be request-throttled mid-run
- **AND** the Worker Run records `budget_override=true` and the acknowledgement for audit
- **AND** post-run reconciliation may report an overrun after native usage evidence is imported

### Requirement: Recoverable launch errors clear on successful retry
The system SHALL overwrite stale recoverable launch-error metadata on each launch attempt and SHALL clear the user-visible launch error after a successful retry or successful Worker Run completion.

#### Scenario: Successful retry clears timeout message
- **WHEN** a task has `launch_error` and `last_launch_failure` from a previous Worker timeout
- **AND** the operator launches the task again and the Worker Run starts successfully
- **THEN** the task no longer renders the previous timeout as the current launch error
- **AND** the successful session evidence is recorded normally when the Worker Run completes

### Requirement: Launch starts asynchronous Worker Run
The system SHALL treat Launch as the start of a governed asynchronous Worker Run rather than completion of the entire Worker Adapter command.

#### Scenario: Launch returns while worker command continues
- **WHEN** an Estimated task passes Launch Guardrails
- **AND** the selected Worker Adapter command starts successfully
- **THEN** the task moves to Running
- **AND** the launch response returns before the Worker Adapter command exits
- **AND** the command continues under the associated Worker Run

### Requirement: Worker completion enters Review
The system SHALL transition successful governed Worker execution into Review instead of leaving standard launches indefinitely in Running.

#### Scenario: Standard worker run completes
- **WHEN** a standard Worker Run exits successfully
- **AND** required tracking evidence is present
- **THEN** the task moves from Running to Review
- **AND** the task retains its session association and run evidence

### Requirement: OpenCode launch uses non-interactive run command
The system SHALL launch OpenCode Worker Sessions through a non-interactive command that includes the `run` subcommand, the task-bound connected project directory, the selected Worker model, JSON output mode, and the scoped task prompt.

#### Scenario: OpenCode launch command includes project root, model, and prompt
- **WHEN** an Estimated task passes Launch Guardrails for the OpenCode Worker Adapter
- **AND** the task is bound to a connected project root
- **THEN** the Local Runner command plan invokes `opencode run`
- **AND** the command plan includes `--dir` with the task-bound connected project root
- **AND** the command plan cwd is the task-bound connected project root
- **AND** the command plan includes `--model` with the selected allowed Worker model
- **AND** the command plan includes the scoped task prompt
- **AND** the command plan is recorded with secrets redacted

#### Scenario: Bare OpenCode template is normalized or rejected
- **WHEN** an existing OpenCode adapter configuration contains a bare launch template equivalent to `opencode`
- **THEN** the system does not launch that bare command for a task run
- **AND** the system either normalizes it to the supported non-interactive run command with the task-bound connected project root or blocks launch with a clear compatibility reason

#### Scenario: Nonzero OpenCode exit preserves useful evidence
- **WHEN** OpenCode exits nonzero after the command plan is launched
- **THEN** the Worker Run is marked failed
- **AND** the task returns to Estimated with retryable launch evidence
- **AND** the task metadata preserves sanitized return code, stdout, stderr, selected adapter, selected model, project root/workdir, and command plan

### Requirement: Governed Worker launch includes Repo Context Brief
The system SHALL include the Repo Context Brief in the Worker launch prompt for connected-project governed Worker Runs before task-specific instructions.

#### Scenario: Launch prompt includes repo context
- **WHEN** an Estimated task for a connected project passes Launch Guardrails
- **AND** the system builds a Repo Context Brief
- **THEN** the Worker Adapter command prompt includes the brief before the task description
- **AND** the prompt tells the Worker to inspect existing relevant files before editing

### Requirement: Governed Worker launch records repo-context event
The system SHALL record Worker Run timeline events for Repo Context Brief creation during governed Worker launch.

#### Scenario: Repo context event is recorded
- **WHEN** the system builds and injects a Repo Context Brief for a governed Worker Run
- **THEN** the Worker Run timeline records a repo-context event with sanitized source names and bounded detail

### Requirement: Governed Worker launch preserves model-layer separation in events
The system SHALL label launch events so operators can distinguish control-plane/orchestrator decisions from Worker/coding harness execution.

#### Scenario: Operator reads launch timeline
- **WHEN** an operator views a governed Worker Run timeline
- **THEN** guardrail, repo-context, and prompt-construction events are labeled as control-plane/orchestrator activity
- **AND** adapter subprocess, native/proxy usage, and file evidence events are labeled as Worker/coding harness activity

### Requirement: Claude Code native usage launch accounting
The system SHALL launch Claude Code Worker Sessions in `native_usage` mode through non-interactive Claude Code command templates and SHALL record cache-inclusive token usage and actual cost from Claude Code result JSON.

#### Scenario: Claude Code native launch records result usage
- **WHEN** an Estimated Task is launched with the Claude Code Worker Adapter in `native_usage` mode
- **AND** Claude Code exits successfully and emits result JSON containing `session_id`, `usage`, `modelUsage`, and `total_cost_usd`
- **THEN** the system records Worker execution usage from the Claude Code result evidence
- **AND** the recorded prompt-side tokens include `input_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens`
- **AND** the recorded completion tokens include `output_tokens`
- **AND** the recorded cost uses `total_cost_usd` or matching `modelUsage` cost evidence
- **AND** the Worker Run records native usage evidence on the Worker/coding harness layer

#### Scenario: Claude Code native launch without evidence is recoverable failure
- **WHEN** a Claude Code `native_usage` Worker Run exits successfully but does not emit trustworthy usage and cost evidence
- **THEN** the Worker Run SHALL fail with missing native usage evidence
- **AND** the Task SHALL return to Estimated with sanitized retryable launch evidence
- **AND** the Task SHALL NOT be moved to Blocked solely because usage evidence was missing after an otherwise launchable attempt

#### Scenario: Claude Code native launch does not claim runtime request governance
- **WHEN** a Worker Run uses Claude Code with `native_usage` tracking mode
- **THEN** the Portal and Worker Run evidence SHALL present the run as budget-authoritative after native usage import
- **AND** the system SHALL NOT label it as runtime request-governed by the Harness Proxy
