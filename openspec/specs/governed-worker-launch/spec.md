# governed-worker-launch Specification

## Purpose
Define how the harness launches local Worker Sessions under governance, including read-only proof runs, write-capable git guardrails, model selection, verification, commits, optional pull requests, and failure evidence preservation.

## Requirements

### Requirement: Read-only launch proof
The system SHALL support a first read-only Worker Session that inspects the connected repository and produces a session report artifact without modifying repository files, using either proxy-governed or native-usage tracking mode.

#### Scenario: Read-only session succeeds through proxy-governed tracking
- **WHEN** OpenCode runs the read-only repo inspection task through the Harness Proxy
- **THEN** the system records Worker token usage, saves a session report artifact with language, test command, and top-level structure, and leaves the repository without file changes

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
The system SHALL preserve evidence when Worker execution cannot complete successfully.

#### Scenario: Worker session fails
- **WHEN** OpenCode crashes, exits non-zero, times out, exceeds budget, fails verification, or produces no budget-authoritative token usage for the selected tracking mode
- **THEN** the Task moves to Blocked and the system preserves logs, token ledger entries when present, failure reason, tracking mode, branch name, and any uncommitted diff without automatic retry

### Requirement: Worker launch model selection
The system SHALL launch Worker Sessions with a model selected from the verified adapter's discovered model inventory unless the User explicitly supplies a compatible override.

#### Scenario: User selects discovered Worker model
- **WHEN** the User launches a task with a model discovered for the selected verified Worker Adapter
- **THEN** the Local Runner passes that model to the Worker Harness launch command and records it on the Worker session

#### Scenario: Selected model is unavailable
- **WHEN** the selected model is not in the selected adapter's discovered model inventory and no explicit compatible override is approved
- **THEN** the system blocks launch and shows the model compatibility reason
