## ADDED Requirements

### Requirement: Codex native verification can bypass Codex git preflight without weakening evidence checks
The system MAY include Codex's supported git-repo-check bypass in Codex native usage verification command plans so verification can run in Harness-controlled temporary or project-independent workdirs, but verification SHALL still pass only when Codex emits trustworthy run-bound native usage evidence.

#### Scenario: Codex verification command includes skip git repo check
- **WHEN** the system verifies Codex in `native_usage` mode for an allowed Codex model
- **THEN** the command plan SHALL invoke `codex exec`
- **AND** the command plan SHALL request machine-readable JSONL output with `--json`
- **AND** the command plan MAY include `--skip-git-repo-check`
- **AND** the command plan SHALL pass the selected Worker model with a Codex-supported model flag
- **AND** the command plan SHALL record sanitized command evidence

#### Scenario: Skip git repo check is not verification evidence
- **WHEN** Codex verification uses `--skip-git-repo-check`
- **AND** Codex returns the required sentinel output but does not emit trustworthy run-bound `turn.completed.usage` evidence
- **THEN** the system SHALL NOT record a budget-authoritative adapter verification token row
- **AND** the adapter verification SHALL remain failed or `observed_only`
- **AND** the adapter SHALL NOT become launchable for normal governed Tasks
