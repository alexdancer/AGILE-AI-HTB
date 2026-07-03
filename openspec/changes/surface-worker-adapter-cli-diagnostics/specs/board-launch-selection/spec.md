## ADDED Requirements

### Requirement: Board shows actionable native CLI launch failures
The AGILE Board SHALL show a concise, sanitized, user-facing diagnostic on the affected task card when a retryable Worker Run fails because the native Worker CLI reports an actionable authentication, trust, or configuration prerequisite.

#### Scenario: Codex trusted-directory failure shown on task card
- **WHEN** an Estimated task is launched with the Codex Worker Adapter
- **AND** the Codex process exits nonzero with `Not inside a trusted directory and --skip-git-repo-check was not specified.` or equivalent sanitized evidence
- **THEN** the task returns to the Estimated column
- **AND** the task card shows a retryable launch failure summary naming the Codex trusted-directory prerequisite
- **AND** the task card includes the selected adapter, selected model, and connected project root context when available
- **AND** the task card still shows the launch form for retry

#### Scenario: Board links adapter setup for adapter prerequisite failures
- **WHEN** a retryable launch failure is caused by a Worker Adapter CLI prerequisite or verification/setup issue
- **THEN** the task card includes a link to `/settings/workers`
- **AND** the link does not replace the inline failure summary on the task card

#### Scenario: Raw launch output remains bounded
- **WHEN** the board renders a native CLI launch failure summary
- **THEN** raw stdout, stderr, and command-plan evidence are either collapsed behind details or shown in a bounded diagnostic block
- **AND** secrets and session credentials are redacted before display
