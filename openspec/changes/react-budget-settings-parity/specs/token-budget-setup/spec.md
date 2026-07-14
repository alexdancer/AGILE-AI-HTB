## ADDED Requirements

### Requirement: Budget setup state has an authenticated JSON read
The Portal SHALL expose the current token budget setup state through an authenticated JSON read that reuses the existing effective-budget computation, so an authenticated operator surface can display caps and today's counter without recomputing budget rules or reading `guardrails.yaml` directly.

#### Scenario: Budget state read requires authentication
- **WHEN** an unauthenticated caller requests the budget setup state read while portal auth is required
- **THEN** the Portal SHALL reject the request using the existing Portal authentication boundary
- **AND** SHALL NOT return budget setup state

#### Scenario: Budget state read reuses authoritative computation
- **WHEN** an authenticated caller requests the budget setup state read
- **THEN** the response SHALL be derived from the same effective-budget computation used by the existing budget surface
- **AND** it SHALL report the daily governed cap, per-session Worker cap, current-window used and remaining tokens, `budget_since`, and last daily-usage reset timestamp
- **AND** absent cap or counter values SHALL be reported as typed `null` rather than fabricated zeros

### Requirement: Budget save and reset actions offer a sanitized negotiated outcome
The token budget save action and the daily-counter reset action SHALL offer a sanitized, content-negotiated JSON outcome to non-HTML callers while preserving the existing HTML redirect behavior for browser form callers. Cap validation and the soft-reset evidence-preservation guarantees SHALL remain authoritative for both caller types.

#### Scenario: Non-HTML save returns a sanitized outcome
- **WHEN** a caller negotiating `application/json` submits valid caps to the budget save action
- **THEN** the Portal SHALL persist the budget using the existing authoritative save behavior
- **AND** SHALL return a bounded JSON outcome carrying the saved authoritative state
- **AND** SHALL NOT redirect that caller to `/setup`

#### Scenario: Non-HTML save rejects invalid caps without leaking internals
- **WHEN** a caller negotiating `application/json` submits an invalid or non-positive cap value
- **THEN** the Portal SHALL return a sanitized error outcome envelope
- **AND** raw exception or stack detail SHALL NOT appear in the outcome
- **AND** the persisted budget SHALL remain unchanged

#### Scenario: Non-HTML reset returns a sanitized outcome and preserves evidence
- **WHEN** a caller negotiating `application/json` submits the daily-counter reset action
- **THEN** the Portal SHALL reset the daily counter using the existing soft-reset behavior
- **AND** all token ledger evidence, session reports, task `actual_tokens`, raw provider evidence, and historical audit views SHALL remain preserved
- **AND** the Portal SHALL return a bounded JSON outcome carrying the refreshed counter state

#### Scenario: HTML form callers keep existing redirects
- **WHEN** a browser form caller submits the save or reset action without negotiating `application/json`
- **THEN** the Portal SHALL preserve the existing redirect behavior for that action
- **AND** the negotiated JSON path SHALL NOT change the HTML caller experience
