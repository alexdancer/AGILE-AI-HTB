## MODIFIED Requirements

### Requirement: Curated control-plane model list has a single authoritative source
The curated control-plane provider/model choices SHALL be defined in a single authoritative source that every renderer consumes, so the authenticated JSON read and the React Control Plane Settings view present the same curated dropdown without divergent copies.

#### Scenario: Every renderer reads the same curated list
- **WHEN** the authenticated control-plane state JSON and the React Control Plane Settings view render the curated model dropdown
- **THEN** each SHALL derive its curated provider/model choices from the same authoritative source
- **AND** no renderer SHALL hard-code an independent copy of the curated list

#### Scenario: Adding a curated model updates every renderer
- **WHEN** a curated provider/model choice is added to or removed from the authoritative source
- **THEN** the JSON read and the React view SHALL reflect that change without a per-renderer edit
