## ADDED Requirements

### Requirement: Dashboard shows operator next actions
The dashboard SHALL show an operator next-actions panel above the existing KPI cards. The panel SHALL summarize workflow actions derived from existing setup, task, and alarm state.

#### Scenario: Dashboard renders next-actions panel
- **WHEN** an authenticated operator opens `/dashboard`
- **THEN** the dashboard shows an operator next-actions panel before budget/session/alarm KPI cards

### Requirement: Dashboard highlights missing Worker launch setup
The next-actions panel SHALL include a Worker setup action when no launchable Worker adapter is available. The action SHALL link to the existing Worker adapters setup page.

#### Scenario: No launchable Worker adapter
- **WHEN** no Worker adapter is launchable
- **THEN** the next-actions panel shows a Worker setup action
- **AND** the action links to `/settings/workers`

### Requirement: Dashboard highlights launchable task work
The next-actions panel SHALL include a launch action when one or more tasks are ready for launch from the board. The action SHALL show the task count and link to the existing task board.

#### Scenario: Tasks are ready to launch
- **WHEN** one or more tasks have launch-ready board status
- **THEN** the next-actions panel shows the number of tasks ready to launch
- **AND** the action links to `/board`

### Requirement: Dashboard highlights review work
The next-actions panel SHALL include a review action when one or more tasks are awaiting operator review. The action SHALL show the task count and link to the existing task board.

#### Scenario: Tasks await review
- **WHEN** one or more tasks are in Review
- **THEN** the next-actions panel shows the number of tasks awaiting review
- **AND** the action links to `/board`

### Requirement: Dashboard highlights alarm work
The next-actions panel SHALL include an alarm action when open alarms exist. Critical or high severity alarms SHALL be identified separately from non-critical open alarms.

#### Scenario: Critical alarms exist
- **WHEN** one or more unresolved alarms have critical or high severity
- **THEN** the next-actions panel shows a critical alarm action with the critical count
- **AND** the action links to `/alarms`

#### Scenario: Only non-critical open alarms exist
- **WHEN** unresolved alarms exist
- **AND** none have critical or high severity
- **THEN** the next-actions panel shows an open alarm action with the open alarm count
- **AND** the action links to `/alarms`

### Requirement: Dashboard always provides board access
The next-actions panel SHALL include a fallback action to open the task board so operators always have an obvious path to estimate, launch, refresh, review, or block tasks.

#### Scenario: No urgent actions exist
- **WHEN** there are no setup, launch, review, or alarm actions to highlight
- **THEN** the next-actions panel still shows an action linking to `/board`
