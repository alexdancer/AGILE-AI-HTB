## ADDED Requirements

### Requirement: Worker Adapter public setup matrix
The public onboarding documentation SHALL provide a Worker Adapter setup matrix for first-class adapter families.

#### Scenario: Operator reads Worker Adapter matrix
- **WHEN** an operator reads public Worker setup guidance
- **THEN** the matrix SHALL cover OpenCode, Claude Code, Codex, and Hermes
- **AND** each row SHALL separate adapter identity, Worker CLI auth source, available tracking modes, launchable evidence, and common failure modes

#### Scenario: Matrix distinguishes tracking modes
- **WHEN** the matrix describes `proxy_governed`, `native_usage`, or `observed_only`
- **THEN** it SHALL state whether runtime request guardrails are available and whether accounting is budget-authoritative
- **AND** it SHALL state that `observed_only` is diagnostic-only and not launchable from the normal AGILE Board

## MODIFIED Requirements

### Requirement: Worker Setup preserves model layer separation
The Worker Setup page and public setup guidance SHALL configure Worker/coding harness adapters and SHALL NOT present the control-plane API key or any generic provider API key as native Worker Adapter authentication.

#### Scenario: Operator configures OpenCode worker adapter
- **WHEN** an operator selects OpenCode on the Worker Setup page or reads OpenCode setup guidance
- **THEN** the page or guidance asks for Worker Adapter setup inputs such as project folder, model discovery/selection, and token-tracking verification
- **AND** the page or guidance does not ask for a generic `PROVIDER_API_KEY` as if it were required for native Worker setup

#### Scenario: Operator already configured control-plane key
- **WHEN** an operator has pasted a control-plane API key through `/settings/control-plane`
- **THEN** Worker setup guidance SHALL still state that native OpenCode, Claude Code, Codex, Hermes, or other Worker CLIs may require their own installed CLI auth/config
- **AND** it SHALL NOT imply that the control-plane API key automatically configures those Worker CLIs
