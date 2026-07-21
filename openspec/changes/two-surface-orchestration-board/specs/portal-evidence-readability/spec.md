## ADDED Requirements

### Requirement: Board evidence reuses the Session Report evidence components
The Evidence Drawer and the Session Report SHALL render task evidence from a single shared implementation rather than parallel copies. The board SHALL NOT embed a second full copy of Session Report evidence on task cards; the Session Report at `/sessions/{session_id}` SHALL remain the permalink and full audit view.

#### Scenario: Drawer mounts the shared evidence components
- **WHEN** an operator opens the Evidence Drawer for a task with session evidence
- **THEN** the drawer SHALL render evidence using the same exported components the Session Report uses
- **AND** the board SHALL NOT maintain a separate inline copy of that evidence

#### Scenario: Session Report remains the full audit permalink
- **WHEN** an operator opens `/sessions/{session_id}`
- **THEN** the Session Report SHALL render the complete evidence paths as the permalink audit view
- **AND** the drawer and the report SHALL stay consistent because they share one evidence implementation
