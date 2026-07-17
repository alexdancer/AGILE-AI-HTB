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

### Requirement: Alarm inbox exposes backend-computed context-aware actions
The system SHALL compute an explicit `available_actions` list for each alarm on the backend and expose it to the authenticated React inbox, so the inbox presents only actions valid for that alarm's type and session state. React SHALL NOT infer action eligibility on its own.

#### Scenario: Every open alarm offers Continue
- **WHEN** the authenticated Alarms inbox loads an open alarm
- **THEN** `available_actions` for that alarm SHALL include `continue`
- **AND** choosing Continue SHALL resolve the alarm through the existing alarm resolution path without deleting the alarm row

#### Scenario: Budget alarm offers Raise Budget targeting the exceeded cap
- **WHEN** the authenticated Alarms inbox loads an open `DAILY_CAP_EXCEEDED` alarm
- **THEN** `available_actions` SHALL include a `raise_budget` action whose target cap key is `daily_cap_tokens`
- **AND** the action SHALL carry the current cap value derived from the alarm's own context
- **WHEN** the alarm is `SESSION_CAP_EXCEEDED`
- **THEN** the `raise_budget` action's target cap key SHALL be `session_cap_tokens`

#### Scenario: Non-budget alarm does not offer Raise Budget
- **WHEN** the authenticated Alarms inbox loads an open alarm that is not a budget cap alarm
- **THEN** `available_actions` SHALL NOT include `raise_budget`

#### Scenario: Inbox does not offer Abort Session or generic guardrail editing
- **WHEN** the authenticated Alarms inbox loads any alarm
- **THEN** `available_actions` SHALL NOT include `abort_session`
- **AND** `available_actions` SHALL NOT include `adjust_guardrail`
- **AND** the inbox SHALL route operators to Guardrail configuration for generic guardrail changes

### Requirement: Raise Budget enforces a positive cap on the backend
The `raise_budget` resolution SHALL reject a new cap value that is not strictly greater than the current cap for the targeted key before applying it. The check SHALL be enforced by the backend resolution path, not only by the React client.

#### Scenario: Raise above current cap is applied
- **WHEN** an operator submits `raise_budget` with a new cap value strictly greater than the current cap for the targeted key
- **THEN** the system SHALL merge the new cap into the session's `guardrail_overrides.budget` for that key using the existing raise-budget behavior
- **AND** the alarm SHALL be resolved with recorded action history

#### Scenario: Raise at or below current cap is rejected
- **WHEN** an operator submits `raise_budget` with a new cap value less than or equal to the current cap for the targeted key
- **THEN** the backend SHALL reject the action and return a sanitized error outcome to the caller
- **AND** the system SHALL NOT change the session budget override
- **AND** the alarm SHALL remain open

### Requirement: Alarm inbox provides bookmarkable open and resolved history filters
The authenticated Alarms inbox SHALL provide bookmarkable Open, Resolved, and All filters that default to Open, while keeping resolved alarms out of the default open view. Resolved entries SHALL surface their resolution evidence.

#### Scenario: Default filter shows only open alarms
- **WHEN** an authenticated operator opens the Alarms inbox without selecting a filter
- **THEN** the inbox SHALL show only unresolved alarms
- **AND** the selected filter SHALL default to Open

#### Scenario: Resolved filter shows resolution evidence
- **WHEN** an authenticated operator selects the Resolved filter
- **THEN** the inbox SHALL show resolved alarms with their resolved action, a sanitized payload summary, `resolved_at`, and a Session Report link
- **AND** the selected filter SHALL be reflected in a bookmarkable query so the view is deep-linkable

#### Scenario: All filter shows open and resolved together
- **WHEN** an authenticated operator selects the All filter
- **THEN** the inbox SHALL show both open and resolved alarms
- **AND** resolved alarms SHALL retain their session id, type, severity, context, and recommended action evidence

### Requirement: React alarm data handoff requires Portal authentication
The React Alarms inbox data handoff SHALL require Portal authentication and SHALL NOT draw inbox data from the existing open `/alarms` JSON route. The negotiated resolve action reuses the shared `/alarms/{alarm_id}/resolve` route and inherits that route's existing authentication boundary — this change SHALL NOT tighten or loosen resolve-route authentication. Backend validation, including the positive-cap guard, remains authoritative regardless of caller authentication.

#### Scenario: React alarms handoff requires authentication
- **WHEN** an unauthenticated caller requests the authenticated React Alarms JSON handoff
- **THEN** the system SHALL reject the request using the Portal authentication boundary
- **AND** SHALL NOT return alarm inbox data

#### Scenario: Legacy JSON alarm route is unchanged
- **WHEN** an API client requests the existing general `/alarms` JSON route or resolves through `/alarms/{alarm_id}/resolve`
- **THEN** the route SHALL keep its current behavior and auth boundary
- **AND** this change SHALL NOT alter that route's authentication

