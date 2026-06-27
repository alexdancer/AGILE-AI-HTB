## ADDED Requirements

### Requirement: Portal supports compact text utilities
The Portal SHALL provide shared server-rendered styling utilities for compact previews of long operator-facing text while preserving access to the full text where the page owns the evidence.

#### Scenario: Touched templates reuse compact text classes
- **WHEN** a touched Portal template needs to display long task, report, command, project, result, or evidence text as a preview
- **THEN** the template SHALL use shared classes for line clamping, wrap-anywhere text, or bounded raw blocks instead of adding one-off inline truncation styles

#### Scenario: Full text remains accessible
- **WHEN** compact text utilities hide overflow in a session or report surface
- **THEN** the same page SHALL provide access to the full text through existing content, native disclosure, or a bounded raw evidence section

#### Scenario: No frontend build step is introduced
- **WHEN** the compact session report change is implemented
- **THEN** the Portal SHALL remain renderable through the existing FastAPI/Jinja server-rendered stack without React, Vite, SPA routing, or a Node-based frontend build pipeline
