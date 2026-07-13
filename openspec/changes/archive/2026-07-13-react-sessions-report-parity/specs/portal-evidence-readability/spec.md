## ADDED Requirements

### Requirement: React Sessions preserves compact list parity
The React Sessions list SHALL preserve the existing compact-first operator scan fields while using bounded pagination and active-only refresh.

#### Scenario: React Sessions row preserves scan fields
- **WHEN** an operator opens the built React `/sessions` surface
- **THEN** each row SHALL show session link, session kind, bounded task preview, model, status, prompt/completion/provider token totals, Worker Run count, Worker event count, failed-checkpoint count, budget zone, and alarm count
- **AND** Agent Review sessions SHALL remain distinguishable from Worker Sessions without opening the report

#### Scenario: Empty, loading, and failure states remain actionable
- **WHEN** Sessions data is loading, absent, or temporarily unavailable
- **THEN** React SHALL show a semantic loading, empty, or sanitized retryable error state
- **AND** a failed refresh SHALL preserve the last successfully loaded rows rather than clearing evidence

#### Scenario: Sessions pagination remains keyboard operable
- **WHEN** more rows exist than the current bounded page
- **THEN** the view SHALL provide labeled keyboard-operable pagination controls
- **AND** status and refresh announcements SHALL not rely on color alone

### Requirement: React Session Report preserves complete evidence paths
The React Session Report SHALL preserve information parity with the current Jinja report. It SHALL present a concise session/launch/review summary first and keep every bounded audit-detail path available without requiring the Jinja report.

#### Scenario: Worker Session report starts with governance summary
- **WHEN** an operator opens a Worker Session report
- **THEN** the report SHALL show task/project, Worker Adapter, Worker model, tracking mode, status/result, review-needed state, token totals, alarm/checkpoint state, and evidence counts before raw evidence
- **AND** missing authoritative usage, Worker Run, project, tracking, or review evidence SHALL remain explicit

#### Scenario: Agent Review report starts with review summary
- **WHEN** an operator opens an Agent Review session report
- **THEN** the report SHALL identify it as control-plane Agent Review evidence
- **AND** it SHALL show reviewed-task context, review model, status, recommendation or failure, review token usage, and missing evidence before raw details

#### Scenario: Token audit paths remain available
- **WHEN** a report has token evidence
- **THEN** React SHALL show provider prompt/completion/raw totals, normalized budget total, all fixed spend categories, Worker token components and cost when available, and paged token-log rows
- **AND** each token row SHALL keep bounded redacted raw provider usage behind disclosure
- **AND** cache-read/reused-context evidence and Agent Review/control-plane usage SHALL remain labeled separately from normalized Worker actuals

#### Scenario: Worker execution audit paths remain available
- **WHEN** a report has Worker Run evidence
- **THEN** React SHALL show the paged chronological Worker Run timeline with level, layer, kind, title, detail summary, and bounded redacted details
- **AND** it SHALL show each Repo Context Brief's Worker Run id, pageable source documents/manifests, and bounded redacted brief-text preview with full continuation when truncated
- **AND** concise failure/retry evidence SHALL appear before raw details

#### Scenario: Governance and review audit paths remain available
- **WHEN** a report has guardrail snapshots, alarms, checkpoint results, or related Agent Review metadata
- **THEN** React SHALL show the paged budget-zone timeline, alarm severity/type/action evidence, checkpoint name/pass/detail evidence, and related Agent Review status/recommendation/summary/model/time/session/tokens/error plus pageable findings
- **AND** related Agent Review tokens SHALL remain review/control-plane evidence separate from Worker execution totals

#### Scenario: Dense evidence is secondary but reachable
- **WHEN** full task text, launch target, raw usage, timeline details, Repo Context Brief text, checkpoint details, or review findings are present
- **THEN** React SHALL keep them in semantic disclosure or bounded raw-evidence regions after the summary
- **AND** every top-level/nested collection SHALL expose `Load more` while authoritative rows remain
- **AND** every truncated text preview SHALL visibly identify truncation and expose its generated authenticated full-text action
- **AND** no task, launch/result text, raw usage/detail, Repo source/text, checkpoint detail, or Agent Review summary/error/finding visible in Jinja SHALL become inaccessible when React is built

### Requirement: React Sessions refreshes only while active
The React Sessions list SHALL poll its bounded list endpoint only while at least one session is `active` or `running`.

#### Scenario: Active list refreshes
- **WHEN** Sessions state reports at least one active/running session
- **THEN** React SHALL request refreshed list state no more often than every 5 seconds
- **AND** a successful response SHALL update rows without a full-page reload

#### Scenario: List polling stops
- **WHEN** no active/running session remains or the operator leaves the Sessions view
- **THEN** React SHALL stop Sessions polling
- **AND** the behavior SHALL NOT establish polling for unrelated Portal surfaces

### Requirement: Active Session Report uses explicit freshness refresh
An active React Session Report SHALL poll only lightweight freshness metadata. It SHALL NOT replace report content until the operator explicitly requests Refresh.

#### Scenario: New evidence produces a notice
- **WHEN** freshness version differs from the version of the displayed report
- **THEN** React SHALL announce `New session evidence available`
- **AND** it SHALL show a keyboard-operable Refresh action
- **AND** it SHALL preserve the displayed report, disclosure state, and reading position until that action succeeds

#### Scenario: Explicit Refresh replaces authoritative report
- **WHEN** the operator activates Refresh after new evidence is available
- **THEN** React SHALL request the full report projection
- **AND** it SHALL replace report state only after a successful response
- **AND** failure SHALL preserve current evidence and show a sanitized retryable error

#### Scenario: Terminal freshness stops polling
- **WHEN** freshness reports a status other than `active` or `running`
- **THEN** React SHALL stop report freshness polling
- **AND** a final changed version SHALL keep the new-evidence notice available for explicit Refresh

#### Scenario: Unchanged freshness does not disturb report
- **WHEN** the freshness version matches the displayed report
- **THEN** React SHALL make no report-content change and SHALL not reset focus, scroll position, or expanded disclosures

#### Scenario: Freshness promise is limited to append and status revisions
- **WHEN** active session status or included append/update revision markers change
- **THEN** the freshness version SHALL change and drive the explicit notice behavior
- **AND** the UI SHALL NOT claim that lightweight polling detects arbitrary in-place raw-evidence or related Agent Review metadata edits without an included revision marker

### Requirement: React Session evidence remains practically accessible
The React Sessions and Session Report surfaces SHALL preserve practical desktop accessibility within the existing Portal design system.

#### Scenario: Report structure is semantic and non-color-only
- **WHEN** an operator reads a React Session Report
- **THEN** the view SHALL use semantic headings, tables/lists, labeled controls, visible focus, and native disclosure behavior
- **AND** status, severity, review-needed state, freshness, errors, and truncation SHALL use text in addition to color

#### Scenario: Async state is announced
- **WHEN** list polling, report freshness, explicit refresh, pagination, or retry changes visible state
- **THEN** concise status/error notices SHALL be exposed through an appropriate live region
- **AND** background unchanged polling SHALL not repeatedly announce noise
