# native-worker-model-discovery Specification

## Purpose
Define how AGILE-AI-HTB discovers and records models available to local Worker Harnesses using the Worker Harness's native CLI and configuration.

## Requirements

### Requirement: Native Worker model discovery
The system SHALL discover models available to a local Worker Harness through that harness's native configuration and CLI capabilities.

#### Scenario: Discover OpenCode models
- **WHEN** OpenCode is installed and callable on the Local Runner
- **THEN** the system can run native discovery and persist the provider/model identifiers that OpenCode reports as available

#### Scenario: Discovery fails
- **WHEN** a Worker Harness model discovery command fails or returns an unsupported format
- **THEN** the system records a sanitized failure reason and keeps the adapter visible but not launch-ready for model-specific tasks

### Requirement: Discovered model inventory
The system SHALL persist discovered Worker Harness models with their adapter id, provider/model identifier, discovery timestamp, and availability status.

#### Scenario: Model inventory displayed
- **WHEN** the User views Worker Harness settings
- **THEN** the system shows discovered models for each adapter and indicates when discovery last succeeded or failed

### Requirement: Worker model recommendation constraints
The system SHALL recommend Worker execution models only from models discovered for a verified Worker Harness unless the User manually overrides with an explicit compatible model.

#### Scenario: Estimate with discovered worker models
- **WHEN** the control-plane model estimates a task and a verified Worker Harness has discovered models
- **THEN** the recommendation uses a model from that Worker Harness's discovered model set

#### Scenario: No discovered worker models
- **WHEN** no Worker Harness model inventory is available
- **THEN** the system may estimate task size but does not mark the task launch-ready with a static or assumed Worker model

### Requirement: Discovery is separate from launch verification
The system SHALL treat model discovery as a prerequisite signal, not proof that the Worker Harness can be launched with token tracking.

#### Scenario: Models discovered but tracking unverified
- **WHEN** a Worker Harness reports available models but no tracking mode has been verified
- **THEN** the system shows the models but keeps normal governed launch disabled for that adapter
