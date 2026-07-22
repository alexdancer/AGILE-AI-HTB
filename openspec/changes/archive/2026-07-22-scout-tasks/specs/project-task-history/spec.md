## ADDED Requirements

### Requirement: Project task history exposes canonical Task kind
The authenticated React project task-history handoff SHALL include `task_kind` on each bounded task entry, derived by the canonical Task-kind reader. `task_kind` SHALL be exactly `implementation`, `scout`, or `acceptance_verification`; raw Task metadata SHALL remain excluded. The history card SHALL render a visible Scout label when the value is `scout` without changing lifecycle, archive, evidence, or restore behavior.

#### Scenario: Archived Scout remains distinguishable
- **WHEN** an archived Scout appears in project task history
- **THEN** its bounded task entry contains `task_kind: scout`
- **AND** React renders a visible Scout label alongside existing lifecycle and evidence fields
- **AND** the Task remains restorable through the existing Unarchive action

#### Scenario: Legacy history entry uses canonical fallback
- **WHEN** a history Task lacks `metadata.task_kind`
- **THEN** a valid legacy `task_breakdown_kind` is preserved
- **AND** an otherwise-untyped legacy Task is projected as `implementation`
- **AND** the browser never receives raw metadata to derive kind itself
