# alarm-inbox Specification

## Purpose
TBD - created by archiving change dismiss-alarms-from-ui. Update Purpose after archive.
## Requirements
### Requirement: Alarm inbox supports dismiss without archive
The Portal alarm inbox SHALL let an authenticated operator dismiss an open alarm from the default UI by resolving or acknowledging it through the existing alarm lifecycle, without deleting the alarm record and without recording alarm archive state.

#### Scenario: Operator dismisses open alarm
- **WHEN** an authenticated operator chooses Dismiss on an open alarm in the Portal alarm inbox
- **THEN** the system SHALL mark the alarm resolved using the alarm resolution path
- **AND** the system SHALL record action history for the operator action
- **AND** the system SHALL NOT delete the alarm row
- **AND** the system SHALL NOT write alarm archive state

#### Scenario: Dismissed alarm leaves default inbox
- **WHEN** an alarm has been dismissed or otherwise resolved
- **AND** an authenticated operator opens the default Alarms page
- **THEN** the alarm SHALL NOT appear in the default open alarm list
- **AND** the page SHALL NOT show the resolved alarm in a default "Recently resolved" list

### Requirement: Resolved alarm evidence remains auditable
Resolved or dismissed alarms SHALL remain available through existing audit surfaces, including API filtering and session evidence, after they disappear from the default alarm inbox.

#### Scenario: API lists resolved alarms for audit
- **WHEN** an alarm has been dismissed or otherwise resolved
- **AND** an API client requests alarms with `resolved=true`
- **THEN** the response SHALL include the resolved alarm with its `resolved_at` value
- **AND** the alarm SHALL keep its original session id, type, severity, context, and recommended action evidence

#### Scenario: JSON API behavior remains compatible
- **WHEN** an API client resolves an alarm through `/alarms/{alarm_id}/resolve`
- **THEN** the response SHALL preserve the existing JSON shape containing the updated alarm and recorded action
- **AND** existing non-dismiss resolution actions SHALL keep their current side effects

