## MODIFIED Requirements

### Requirement: Read-only launch proof
The system SHALL support read-only Worker Sessions that inspect the connected repository and produce a session report artifact without modifying repository files, using either proxy-governed or native-usage tracking mode. A Scout SHALL launch only when the selected verified Worker Adapter also has an adapter-enforced read-only profile; tracking authority alone SHALL NOT prove read-only capability. Proxy-governed mode SHALL forward upstream through direct provider clients rather than LiteLLM. Before/after repository checks SHALL remain required defense and audit evidence but SHALL NOT replace pre-execution read-only enforcement.

#### Scenario: Read-only session succeeds through proxy-governed tracking
- **WHEN** OpenCode runs a read-only repo inspection task through the Harness Proxy
- **AND** the OpenCode adapter has a verified adapter-enforced read-only profile
- **THEN** the system records Worker token usage from the direct upstream provider response, saves a session report artifact with findings, risks, and recommendation, and leaves the repository without file changes
- **AND** it records the verified read-only profile and unchanged-repository evidence on the Worker Run

#### Scenario: Read-only session succeeds through native usage tracking
- **WHEN** a verified Worker Adapter runs a read-only repo inspection task through native harness configuration
- **AND** the Local Runner imports trustworthy usage evidence
- **AND** the adapter has a verified adapter-enforced read-only profile
- **THEN** the system records Worker token usage from native usage evidence, saves a session report artifact, records the tracking mode and read-only profile, and leaves the repository without file changes

#### Scenario: Read-only session modifies files
- **WHEN** a read-only Worker Session produces a git diff or file modification despite adapter enforcement
- **THEN** the system marks the session with the existing hard safety Blocked Condition and preserves logs, token usage, read-only profile, and diff evidence
- **AND** it does not describe post-run detection as successful read-only enforcement

#### Scenario: Adapter lacks enforced read-only profile
- **WHEN** an operator attempts to launch a Scout through an otherwise board-launchable adapter without a verified adapter-enforced read-only profile
- **THEN** Launch Guardrails reject the attempt before creating a Worker Run
- **AND** the response identifies the adapter compatibility requirement without exposing configuration secrets
- **AND** the system does not downgrade to prompt-only or detect-after-run safety

#### Scenario: Codex Scout uses native read-only sandbox
- **WHEN** a Scout passes Launch Guardrails for a Codex adapter with verified read-only capability
- **THEN** the Codex command plan uses `codex exec --json` with `--sandbox read-only`, the selected allowed model, the task-bound project root, and the bounded Scout prompt
- **AND** Codex launch normalization does not replace `read-only` with `workspace-write`
- **AND** existing native-usage evidence and model allow-list requirements remain in force

## ADDED Requirements

### Requirement: Scout launch forces read-only mode
Governed launch SHALL derive Scout execution mode from canonical Task kind. A Task with `task_kind: scout` SHALL force `launch_mode: read_only` server-side regardless of client input and SHALL use the normal Worker Run lifecycle.

#### Scenario: Client requests write-capable Scout
- **WHEN** a launch request or stale Task metadata attempts to make a Scout write-capable
- **THEN** the backend ignores or rejects the incompatible mode before starting a Worker process
- **AND** it never creates a Task branch or Harness-owned commit for the Scout

#### Scenario: Scout launch passes ordinary guardrails
- **WHEN** a Scout has a valid estimate, allowed Worker model, board-launchable tracking mode, project binding, budget approval, and verified adapter read-only profile
- **THEN** the system creates the ordinary Session and Worker Run
- **AND** the Worker Run records `task_kind: scout` and `launch_mode: read_only`
- **AND** successful authoritative completion moves the Scout to Review

### Requirement: Read-only capability remains separate from tracking authority
The system SHALL represent adapter-enforced read-only capability separately from Worker Adapter tracking mode and board launchability. `proxy_governed` and `native_usage` SHALL retain their existing accounting meanings, and `observed_only` SHALL remain unavailable for Scout launch.

#### Scenario: Native usage adapter lacks read-only capability
- **WHEN** an adapter is verified for authoritative `native_usage` but has no verified read-only profile
- **THEN** ordinary compatible write-capable Tasks may remain board-launchable under existing rules
- **AND** Scout launch is unavailable for that adapter

#### Scenario: Observed-only adapter advertises read-only command
- **WHEN** an `observed_only` adapter can construct a read-only command but cannot prove authoritative usage
- **THEN** the adapter remains non-launchable from the normal board for Scouts
- **AND** read-only capability does not upgrade tracking authority
