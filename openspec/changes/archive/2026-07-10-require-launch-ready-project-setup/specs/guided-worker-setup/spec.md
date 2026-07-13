## MODIFIED Requirements

### Requirement: Setup pages show the next missing setup action
Setup and Worker Adapter pages SHALL identify the next missing action needed to make the Portal launch-ready. Setup Overview SHALL report overall launch readiness only when Control Plane, Token Budget, and Worker Adapter requirements pass and at least one Connected Project has computed `launch_ready` capability.

#### Scenario: Worker setup highlights next missing action
- **WHEN** an authenticated operator opens Worker Adapter setup and the active adapter is not launchable
- **THEN** the page SHALL show the next missing setup action such as select default adapter, discover models, allow models, verify tracking, or connect/open a project when that context is missing
- **AND** the page SHALL link or focus the existing control that completes that action

#### Scenario: No Connected Project is available
- **WHEN** Control Plane, Token Budget, and Worker Adapter requirements pass
- **AND** no Connected Project exists
- **THEN** Setup Overview SHALL NOT report `Ready to launch`
- **AND** the next action SHALL direct the operator to Project Settings to connect a project

#### Scenario: Connected Projects are not launch-ready
- **WHEN** Control Plane, Token Budget, and Worker Adapter requirements pass
- **AND** Connected Projects exist but each computed Project Capability is analysis-ready or blocked
- **THEN** Setup Overview SHALL NOT report `Ready to launch`
- **AND** the next action SHALL direct the operator to Project Settings

#### Scenario: Local Runner is unavailable despite persisted capability
- **WHEN** Control Plane, Token Budget, and Worker Adapter requirements pass
- **AND** a Connected Project has persisted `launch_ready` capability
- **AND** the Local Runner Execution Backend is disabled or unavailable
- **THEN** Setup Overview SHALL NOT use persisted capability to report `Ready to launch`
- **AND** the next action SHALL direct the operator to Project Settings

#### Scenario: Launch-ready setup shows project board action
- **WHEN** Control Plane, Token Budget, and Worker Adapter requirements pass
- **AND** at least one Connected Project has computed `launch_ready` capability
- **THEN** Setup Overview SHALL show a launch-ready state
- **AND** the primary action SHALL link directly to a launch-ready Connected Project's board

#### Scenario: Earlier setup blocker retains priority
- **WHEN** no Connected Project is launch-ready
- **AND** an earlier Control Plane, Token Budget, or Worker Adapter requirement is also incomplete
- **THEN** Setup Overview SHALL show the earlier incomplete requirement as the next action
- **AND** it SHALL still keep the Connected Project step incomplete
