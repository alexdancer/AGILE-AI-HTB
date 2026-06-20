## MODIFIED Requirements

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
