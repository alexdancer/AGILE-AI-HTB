## ADDED Requirements

### Requirement: React Worker Settings JSON is authenticated, exact, and bounded
FastAPI SHALL expose a new authenticated JSON handoff for Worker Settings that requires Portal authentication and reuses the existing adapter view-model, active-adapter selection, and next-action computation. The response SHALL be bounded and sanitized so the frontend can render adapter configuration, the discover→approve model workflow, readiness, and evidence without recomputing Worker-adapter rules in the browser.

#### Scenario: Worker Settings handoff requires authentication
- **WHEN** an unauthenticated caller requests the authenticated React Worker Settings JSON handoff while portal auth is required
- **THEN** FastAPI SHALL reject the request using the Portal authentication boundary
- **AND** SHALL NOT return Worker Settings data

#### Scenario: Worker Settings JSON is bounded and exact
- **WHEN** an authenticated caller requests the React Worker Settings JSON handoff
- **THEN** the response SHALL include, for each adapter, an allow-listed projection of id, kind, `configured`, `is_default`, connection type, available tracking modes with their view options, discovered models, operator-approved supported models, launchability, sanitized diagnostics, sanitized verification evidence and diagnostic, and the model-discovery label
- **AND** it SHALL include the selected active adapter identifier and a single next-action derived from the same computation the Jinja page uses
- **AND** absent optional values SHALL be typed `null` rather than fabricated defaults

#### Scenario: Worker Settings JSON never leaks raw failure detail
- **WHEN** the Worker Settings JSON handoff serializes diagnostics or verification evidence for an adapter whose detection or verification failed
- **THEN** the response SHALL carry only sanitized evidence bounded by the existing evidence-safety helper
- **AND** it SHALL NOT include raw filesystem paths or raw exception text

### Requirement: React negotiates the redirect-only Worker Settings mutations and consumes the live actions
The existing `POST /settings/workers/{id}/configure`, `POST /settings/workers/{id}/allowed-models`, and `POST /settings/workers/{id}/refresh-diagnostics` actions SHALL return a bounded, sanitized JSON outcome to React/JSON callers while preserving the current Jinja redirects for HTML callers. The existing live `POST /settings/workers/{id}/verify` and `POST /settings/workers/{id}/discover-models` actions SHALL keep their current negotiated JSON outcomes unchanged. Adapter configuration, model discovery, allow-listing, and live verification SHALL remain authoritative for both caller types.

#### Scenario: React caller receives a JSON set-default outcome
- **WHEN** a React/JSON caller marks an adapter as the active default
- **THEN** FastAPI SHALL persist the change using the existing authoritative behavior
- **AND** SHALL return a bounded JSON outcome sufficient for React to refresh authoritative state

#### Scenario: React caller receives a JSON model-approval outcome
- **WHEN** a React/JSON caller approves a subset of discovered models for an adapter
- **THEN** FastAPI SHALL apply the approved subset using the existing behavior that rejects models not yet discovered
- **AND** SHALL return a bounded JSON outcome on success and a sanitized error outcome when approval is rejected

#### Scenario: React refresh-diagnostics error is sanitized
- **WHEN** a React/JSON caller re-detects an adapter binary and detection fails
- **THEN** FastAPI SHALL return a sanitized error outcome envelope
- **AND** raw filesystem paths or exception detail SHALL NOT reach the operator

#### Scenario: React consumes the live verify and discover outcomes unchanged
- **WHEN** a React/JSON caller runs the connection verification or model discovery for an adapter
- **THEN** FastAPI SHALL execute the existing live action and return its existing bounded outcome carrying pass/fail, sanitized reasons, and sanitized evidence
- **AND** the negotiated JSON path SHALL NOT alter those existing action shapes

#### Scenario: HTML callers keep the redirects
- **WHEN** a browser form caller submits any Worker Settings mutation without negotiating `application/json`
- **THEN** FastAPI SHALL preserve the existing redirect behavior for that action, including the existing error query for a rejected model approval
- **AND** the negotiated JSON path SHALL NOT alter that HTML behavior

### Requirement: React Worker Settings navigates inside the shell
React SHALL render Worker Settings inside the shared Portal chrome on the canonical `/settings/workers` URL when the complete build is available, and FastAPI SHALL render the existing Jinja page at the same URL when the build is missing or partial. The view SHALL preserve adapter selection, per-adapter configuration and evidence, the discover→approve model workflow, the live Verify and Discover actions, and the readiness next-action.

#### Scenario: Built canonical route opens React Worker Settings in-shell
- **WHEN** an authenticated operator opens `/settings/workers` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Worker Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated Worker Settings JSON for its adapters, selection, and next-action

#### Scenario: Missing or partial build keeps canonical Worker Settings in Jinja
- **WHEN** an authenticated operator opens `/settings/workers` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja workers page at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Approval is gated behind discovery
- **WHEN** the React Worker Settings view renders an adapter that has no discovered models
- **THEN** the model-approval control SHALL offer only discovered models and SHALL be unavailable until discovery has run for that adapter
- **AND** this SHALL mirror the existing server rule that rejects approval of models not yet discovered

#### Scenario: Live action stays on page with inline outcome and authoritative refetch
- **WHEN** an operator runs Verify or Discover models from the React view
- **THEN** React SHALL show the inline pass/fail outcome and sanitized reasons without leaving the page
- **AND** React SHALL refetch authoritative Worker Settings state and keep the operator on the adapter they were editing rather than resetting to the default adapter

#### Scenario: Set-default and approval stay on page with inline outcome
- **WHEN** an operator marks an adapter as default or approves models from the React view and the action succeeds
- **THEN** React SHALL show an inline success outcome without leaving the page
- **AND** React SHALL refetch authoritative Worker Settings state rather than optimistically trusting the submitted values
