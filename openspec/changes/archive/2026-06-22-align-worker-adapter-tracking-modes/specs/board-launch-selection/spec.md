## MODIFIED Requirements

### Requirement: Launch errors surface inline on board
When a Worker Run fails retryably, the board template SHALL render the failure on the affected task card while preserving the task's Estimated column and launch form. When `launch_task()` rejects a pre-launch guardrail, the route SHALL return the failure reasons in the response or redirect. When the failure is caused by adapter setup or verification, the UI SHALL link the operator to `/settings/workers` for the simplified Worker Setup flow. When a native usage budget override is required, the UI SHALL require acknowledgement that native usage cannot be request-throttled mid-run.

#### Scenario: Budget exceeded on launch
- **WHEN** task estimate exceeds remaining worker_execution budget
- **AND** operator clicks "Launch task" without budget override
- **THEN** the board shows "Task estimate exceeds remaining launch budget" in an error banner

#### Scenario: Native usage budget override requires acknowledgement
- **WHEN** task estimate exceeds remaining worker_execution budget
- **AND** the selected Worker Adapter uses `native_usage` tracking mode
- **AND** operator chooses to launch with budget override
- **THEN** the board requires acknowledgement that native usage cannot be request-throttled mid-run
- **AND** the launched Worker Run records `budget_override=true`
- **AND** post-run reconciliation may report a budget overrun after native usage evidence is imported

#### Scenario: Adapter not launch-ready on launch
- **WHEN** operator clicks "Launch task" with an adapter that is unconfigured, unverified, or observed-only
- **THEN** the board shows the launch guardrail failure reasons in an error banner
- **AND** the banner includes a link to `/settings/workers` to complete Worker Setup

#### Scenario: Successful launch removes error
- **WHEN** a previous error was shown
- **AND** operator loads the board normally (no error query param)
- **THEN** no error banner is displayed

#### Scenario: Recoverable worker failure stays relaunchable
- **WHEN** a Running task's Worker Run fails because the Worker command exits nonzero, times out, or emits no required usage evidence
- **THEN** the task returns to the Estimated column
- **AND** the task card shows the recoverable launch failure message and sanitized evidence
- **AND** the task card still shows the launch form for retry

## ADDED Requirements

### Requirement: Board shows tracking mode strength
The board SHALL show tracking-mode-specific launch copy for the selected Worker Adapter without collapsing all launchable adapters into a generic governed state.

#### Scenario: Native usage adapter selected
- **WHEN** an Estimated task's selected Worker Adapter uses `native_usage` tracking mode
- **THEN** the board shows `Tracking: Tracked via Native Usage`
- **AND** the board shows `Runtime request guardrails: Not available`
- **AND** the board shows `Accounting: Budget-authoritative after run`

#### Scenario: Proxy-governed adapter selected
- **WHEN** an Estimated task's selected Worker Adapter uses `proxy_governed` tracking mode
- **THEN** the board shows `Tracking: Governed via Harness Proxy`
- **AND** the board shows `Runtime request guardrails: Available`
- **AND** the board shows `Accounting: Budget-authoritative during run`

#### Scenario: Observed-only adapter selected
- **WHEN** an Estimated task's selected Worker Adapter uses `observed_only` tracking mode
- **THEN** the board keeps Launch guardrail-blocked
- **AND** the board links the operator to Worker Setup diagnostics instead of launching the Task
