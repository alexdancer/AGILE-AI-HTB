## ADDED Requirements

### Requirement: Codex native launch bypasses Codex git preflight under Harness guardrails
The system SHALL construct Codex native usage Worker launch commands with Codex's supported git-repo-check bypass while preserving Harness-owned task project binding, write-capable git guardrails, model allow-listing, and native usage evidence requirements.

#### Scenario: Codex launch command includes project root and skip git repo check
- **WHEN** an Estimated Task passes Launch Guardrails for the Codex Worker Adapter in `native_usage` mode
- **AND** the task is bound to a connected project root
- **AND** the selected model is in the Codex adapter's operator-approved allowed model subset
- **THEN** the Local Runner command plan SHALL invoke `codex exec`
- **AND** the command plan SHALL include `--json`
- **AND** the command plan SHALL include `--skip-git-repo-check`
- **AND** the command plan SHALL include the selected allowed Codex Worker model with Codex's supported model flag
- **AND** the command plan SHALL set or pass the task-bound connected project root explicitly
- **AND** the command plan SHALL include the scoped task prompt
- **AND** the command plan SHALL be recorded with secrets redacted

#### Scenario: Harness write-capable guardrails still run before Codex
- **WHEN** a write-capable Task is launched with the Codex Worker Adapter
- **AND** the task-bound connected project root fails existing Harness git repository, branch, or clean working tree guardrails
- **THEN** the system SHALL reject the launch before starting any Codex process
- **AND** the rejection SHALL explain the Harness guardrail failure
- **AND** `--skip-git-repo-check` SHALL NOT be treated as permission to bypass Harness write-capable safety checks

#### Scenario: Codex launch still requires native usage evidence
- **WHEN** a Codex Worker Run uses `--skip-git-repo-check`
- **AND** Codex exits successfully without trustworthy run-bound `turn.completed.usage` evidence
- **THEN** the Worker Run SHALL fail with missing native usage evidence
- **AND** the Task SHALL return to Estimated with sanitized retryable launch evidence
- **AND** the adapter's tracking authority SHALL NOT be upgraded or changed by the presence of the bypass flag
