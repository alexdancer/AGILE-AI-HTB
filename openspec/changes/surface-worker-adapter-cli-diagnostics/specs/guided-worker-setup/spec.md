## ADDED Requirements

### Requirement: Worker Setup surfaces actionable native CLI verification failures
Worker Setup SHALL show a concise, sanitized, user-facing diagnostic in the primary readiness summary when the active Worker Adapter's latest verification failed because the native CLI reported an actionable authentication or configuration prerequisite.

#### Scenario: Claude Code login failure shown in setup
- **WHEN** the active Worker Adapter is Claude Code
- **AND** the latest verification evidence contains a native CLI failure equivalent to `Not logged in · Please run /login`
- **THEN** `/settings/workers` shows Claude Code as not launch-ready
- **AND** the primary readiness summary tells the operator to log in to the Claude Code CLI with `/login` or equivalent local CLI auth
- **AND** the operator does not need to expand raw verification JSON to see that next action

#### Scenario: Raw verification details remain secondary
- **WHEN** Worker Setup shows an actionable native CLI verification failure summary
- **THEN** raw stdout, stderr, command plan, and evidence details remain available only in Advanced details or a native disclosure by default
- **AND** secrets and session credentials are redacted before display
