# recorded-demo-run Specification

## Purpose
TBD - created by archiving change playwright-recorded-demo. Update Purpose after archive.
## Requirements
### Requirement: Recorded Demo Run executes unattended without real providers or Worker CLIs

A Recorded Demo Run SHALL be a deterministic, unattended browser run of a Demo Scenario that records
Portal behavior end to end. It MUST NOT require a real model provider, a real Worker Adapter CLI, an
operator secret, or network access to any external service.

#### Scenario: Run completes with no configured provider or Worker CLI

- **WHEN** a Recorded Demo Run executes on a machine with no configured model provider, no installed
  Worker Adapter CLI, and no operator secrets
- **THEN** the run completes and records its evidence without contacting an external service

#### Scenario: Run requires no operator interaction

- **WHEN** a Recorded Demo Run executes
- **THEN** it reaches its terminal state without prompting for input, and every wait resolves on an
  observable state change rather than a fixed elapsed delay

### Requirement: Recorded Demo Run state is isolated and synthetic

A Recorded Demo Run SHALL create its own temporary Git repository, dedicated database, and Portal
credentials for each execution. It MUST NOT read from or write to the operator's working repository,
default database, or configured credentials. All seeded content MUST follow the repository's
synthetic data rules (`DEMO`, `2099`, `999`, `.invalid`). Temporary state MUST be removed when the
run ends, including when it fails.

#### Scenario: Run never targets operator state

- **WHEN** a Recorded Demo Run seeds its Connected Project and database
- **THEN** it uses a freshly created temporary Git repository and a dedicated database file, and the
  operator's working repository and default database are unmodified

#### Scenario: Temporary state is removed after failure

- **WHEN** a Recorded Demo Run fails partway through
- **THEN** the server is stopped, the synthetic substitution is undone, and temporary project and
  database state are removed

#### Scenario: Seeded content is recognizably synthetic

- **WHEN** any seeded project, task, adapter, session, or streamed content is inspected
- **THEN** its identifying values use the repository's synthetic data conventions and contain no
  real identity, credential, or secret

### Requirement: Production exposes no Recorded Demo Run test surface

The application MUST NOT gain any endpoint, route, flag, or environment-driven mode that exists to
support a Recorded Demo Run. Test-only seeding and substitution MUST live in unshipped test code and
MUST NOT be reachable over HTTP. Browser automation MUST drive only normal Portal routes and actions.

#### Scenario: No test reset or seed endpoint exists

- **WHEN** the application is served during a Recorded Demo Run
- **THEN** no HTTP route exposes state reset, state seeding, or synthetic Worker substitution

#### Scenario: No environment mode weakens production behavior

- **WHEN** a Recorded Demo Run configures the application
- **THEN** it does so only through supported settings, and no environment variable disables
  authentication, guardrails, budget enforcement, or evidence rules

#### Scenario: Browser uses only operator-reachable surfaces

- **WHEN** the browser authenticates, navigates, launches, reviews, and completes the scenario
- **THEN** every interaction uses a route and control an ordinary operator can reach in the Portal

### Requirement: Synthetic Worker substitution preserves the governed run path

A Recorded Demo Run SHALL substitute the Worker subprocess execution seam only, so that the launch
route, background run, stream event mapping, event persistence, redaction, final usage parsing,
lifecycle transition, and budget accounting all execute unmodified. The substitution MUST be
established before the application begins serving requests. Test-only instrumentation that preserves
behavior — an observer that calls through to the original and returns its result, or restoration of a
value another test fixture replaced — is permitted, MUST NOT alter any governed outcome, and MUST be
recorded in the change's design.

#### Scenario: Only the subprocess seam is substituted

- **WHEN** a Recorded Demo Run launches a task
- **THEN** the synthetic runner replaces only Worker subprocess execution, and the surrounding
  governed pipeline runs its production code path

#### Scenario: Instrumentation does not alter governed outcomes

- **WHEN** the launcher wraps a production symbol for observation or restores a value replaced by
  another fixture
- **THEN** the wrapper calls through to the original and returns its result unchanged, and the
  governed outcome is identical to an unwrapped run

#### Scenario: Lifecycle and accounting are unchanged by substitution

- **WHEN** the synthetic Worker Run completes
- **THEN** the task transitions to `Review` and its authoritative token total is derived through the
  same final evidence path used for a real Worker Run

### Requirement: Recorded Demo Run proves live streamed Worker evidence in the browser

A Recorded Demo Run SHALL prove that streamed Worker evidence is visible to an operator's browser
**while the task is still `Running`**. The synthetic Worker MUST hold the run open under test control
until the browser assertions complete, so the live state is observed rather than inferred after
completion.

#### Scenario: Streamed agent message is visible while Running

- **WHEN** the synthetic Worker has emitted its sentinel agent message and the run is held open
- **THEN** the browser displays that message as Worker Run evidence while the task status is
  `Running`

#### Scenario: Provisional token evidence is visible while Running

- **WHEN** the synthetic Worker has emitted provisional usage and the run is held open
- **THEN** the browser displays a token figure labeled as provisional while the task status is
  `Running`

#### Scenario: Live evidence is read-only

- **WHEN** streamed Worker evidence is displayed during a run
- **THEN** it is presented as evidence with no reply, acknowledgement, or other operator input
  affordance

#### Scenario: At least one evidence item arrives only through the incremental feed

- **WHEN** the synthetic Worker emits an evidence line after the browser has already loaded the
  board for the running task, with no intervening board reload
- **THEN** that evidence still appears in the browser, proving delivery through the incremental
  event projection rather than through a full board payload

### Requirement: Provisional live usage never displaces authoritative usage

Any token figure shown while a run is in progress MUST be labeled provisional. The authoritative
Worker execution total MUST be the one finalized from the completed run's evidence, and a Recorded
Demo Run SHALL assert that the final recorded total comes from that final evidence rather than from
any provisional streamed value.

#### Scenario: Final total derives from completion evidence

- **WHEN** the synthetic run is released and completes
- **THEN** the recorded actual token total matches the completion evidence, and a provisional value
  emitted earlier in the same stream does not become the authoritative total

#### Scenario: Provisional and final figures are distinguishable

- **WHEN** the browser shows usage during the run and after completion
- **THEN** the in-progress figure is labeled provisional and the post-completion figure is not

### Requirement: Recorded Demo Run finishes through labeled synthetic disposition

After recording `Review` and Session Report evidence, a Recorded Demo Run SHALL invoke the normal
Mark Done action so the scenario finishes in `Done`. This disposition MUST be labeled automated
synthetic disposition. It MUST NOT be described as human acceptance or review, and MUST NOT be
implemented as a backend automatic transition.

#### Scenario: Completion uses the normal operator control

- **WHEN** the run reaches `Review` and has recorded Session Report evidence
- **THEN** the browser invokes the same Mark Done control an operator uses, and the task reaches
  `Done`

#### Scenario: Disposition is labeled synthetic

- **WHEN** the Mark Done step is recorded or described in test text or artifacts
- **THEN** it is identified as automated synthetic disposition rather than human acceptance

#### Scenario: No backend auto-transition is introduced

- **WHEN** a Worker Run reaches `Review` outside a Recorded Demo Run
- **THEN** no automatic transition to `Done` occurs

### Requirement: Recorded Demo Run artifacts are labeled synthetic

Every artifact a Recorded Demo Run produces MUST be labeled synthetic and MUST NOT be presented as
evidence of live Worker Adapter verification, real token usage, human review, or real provider
behavior. Routine runs MUST write only ignored local output; failure diagnostics such as traces and
screenshots are permitted and MUST remain ignored rather than committed.

#### Scenario: Artifacts carry synthetic labeling

- **WHEN** a Recorded Demo Run produces run output, evidence, or diagnostics
- **THEN** each artifact identifies itself as synthetic

#### Scenario: Routine runs commit nothing

- **WHEN** a Recorded Demo Run executes routinely, whether it passes or fails
- **THEN** its output is ignored by version control and no artifact is committed

### Requirement: Synthetically verified fixtures are scoped and labeled

A fixture that seeds a verified Worker Adapter without a real verified CLI MUST label that
verification synthetic wherever it surfaces. Such a fixture MAY seed a launch-ready Connected
Project when it substitutes a synthetic Worker, because a launchable task is required to record
governed execution. A fixture that does **not** substitute a synthetic Worker MUST remain truthfully
`analysis_ready` rather than `launch_ready` when no real Worker Adapter has been verified.

#### Scenario: Synthetic-Worker fixture may be launch-ready

- **WHEN** a Recorded Demo Run seeds a scenario that substitutes a synthetic Worker
- **THEN** it may seed a verified adapter and a launch-ready project, and that verification is
  identified as synthetic

#### Scenario: Non-substituting fixture stays analysis-ready

- **WHEN** a browser fixture does not substitute a synthetic Worker and no real Worker Adapter has
  been verified
- **THEN** the fixture reports `analysis_ready` and does not claim `launch_ready`

### Requirement: First Recorded Demo Run slice starts from an accepted task

The first Recorded Demo Run SHALL begin from a seeded accepted task and cover synthetic governed
launch, live streamed evidence, `Review`, Session Report evidence, and synthetic disposition. The
Markdown intake, Task Breakdown Review, and accepted-estimation path MAY be recorded by a later
change and is NOT required to prove live streamed Worker evidence.

#### Scenario: First slice omits the intake path

- **WHEN** the first Recorded Demo Run executes
- **THEN** it starts from a seeded accepted task and records the launch-through-disposition path
  without requiring a synthetic Control Plane estimation response

#### Scenario: Intake coverage remains a separate change

- **WHEN** full Markdown intake through accepted estimation is required in a recording
- **THEN** it is proposed as a separate change with its own synthetic Control Plane response fixture

