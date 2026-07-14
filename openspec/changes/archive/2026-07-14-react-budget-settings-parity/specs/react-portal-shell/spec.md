## ADDED Requirements

### Requirement: React Budget Settings JSON is authenticated, exact, and bounded
FastAPI SHALL expose a new authenticated JSON handoff for Budget Settings that requires Portal authentication and reuses the existing effective-budget helper. The response SHALL preserve every field the operator needs to configure caps and read today's counter without recomputing budget domain values in the frontend.

#### Scenario: Budget handoff requires authentication
- **WHEN** an unauthenticated caller requests the authenticated React Budget Settings JSON handoff while portal auth is required
- **THEN** FastAPI SHALL reject the request using the Portal authentication boundary
- **AND** SHALL NOT return budget setting data

#### Scenario: Budget JSON uses exact fields derived from existing helpers
- **WHEN** an authenticated caller requests the React Budget Settings JSON handoff
- **THEN** the response SHALL be derived from the existing effective-budget-settings helper without duplicating budget rules in frontend code
- **AND** it SHALL include exactly the daily cap, per-session Worker cap, current-window used tokens, current-window remaining tokens, `budget_since`, and last daily-usage reset timestamp
- **AND** absent cap or counter values SHALL be typed `null` rather than fabricated zeros

### Requirement: React negotiates the budget save and reset outcomes
The existing `POST /settings/budget` and `POST /settings/budget/reset` actions SHALL return a bounded JSON outcome to React/JSON callers while preserving the current Jinja redirects for HTML callers. Backend validation of cap values SHALL remain authoritative for both caller types.

#### Scenario: React caller receives a JSON save outcome
- **WHEN** a React/JSON caller submits valid daily and per-session caps to the budget save action
- **THEN** FastAPI SHALL persist the budget using the existing authoritative behavior
- **AND** SHALL return a bounded JSON outcome sufficient for React to refresh authoritative budget state
- **AND** the outcome SHALL NOT force navigation to `/setup`

#### Scenario: React caller receives a sanitized rejection
- **WHEN** a React/JSON caller submits an invalid or non-positive cap value
- **THEN** FastAPI SHALL return a sanitized error outcome envelope for the caller to surface
- **AND** raw exception text SHALL NOT reach the operator
- **AND** the saved budget SHALL remain unchanged

#### Scenario: React caller receives a JSON reset outcome
- **WHEN** a React/JSON caller submits the daily-counter reset action
- **THEN** FastAPI SHALL reset the daily counter using the existing soft-reset behavior that preserves ledger, session, and task evidence
- **AND** SHALL return a bounded JSON outcome sufficient for React to refresh the counter state

#### Scenario: HTML callers keep the redirects
- **WHEN** a browser form caller submits the budget save or reset action without negotiating `application/json`
- **THEN** FastAPI SHALL preserve the existing redirect behavior for that action
- **AND** the negotiated JSON path SHALL NOT alter that HTML behavior

### Requirement: React Budget Settings navigates inside the shell
React SHALL render Budget Settings inside the shared Portal chrome on the canonical `/settings/budget` URL when the complete build is available, keep `Back to setup` as an ordinary full-page link, and require confirmation before the destructive counter reset. When the React build is missing or partial, FastAPI SHALL render the existing Jinja budget page at the same canonical URL.

#### Scenario: Built canonical route opens React Budget Settings in-shell
- **WHEN** an authenticated operator opens `/settings/budget` while the complete React build is available
- **THEN** FastAPI SHALL serve the React shell and render Budget Settings inside the full Portal chrome
- **AND** React SHALL request the authenticated Budget Settings JSON for its form and counter

#### Scenario: Missing or partial build keeps canonical Budget Settings in Jinja
- **WHEN** an authenticated operator opens `/settings/budget` while the React build is missing or partial
- **THEN** FastAPI SHALL render the existing Jinja budget page at the same canonical URL
- **AND** it SHALL NOT return a blank shell or require an alternate fallback URL

#### Scenario: Save stays on page with inline outcome and authoritative refetch
- **WHEN** an operator saves caps from the React Budget Settings view and the save succeeds
- **THEN** React SHALL show an inline success outcome without leaving the Budget Settings page
- **AND** React SHALL refetch authoritative budget state rather than optimistically trusting the submitted values

#### Scenario: Reset requires confirmation
- **WHEN** an operator triggers the daily-counter reset from the React Budget Settings view
- **THEN** React SHALL require an explicit confirmation before submitting the reset
- **AND** it SHALL surface the outcome inline and refetch authoritative counter state
