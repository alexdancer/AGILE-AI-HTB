## ADDED Requirements

### Requirement: Worker Setup labels tracking mode strength
The Workers settings page SHALL display canonical tracking labels and separate launch readiness from runtime request guardrail availability and accounting authority.

#### Scenario: Proxy-governed adapter label
- **WHEN** Worker Setup renders an adapter verified with `proxy_governed` tracking mode
- **THEN** it shows `Tracking: Governed via Harness Proxy`
- **AND** it shows `Runtime request guardrails: Available`
- **AND** it shows `Accounting: Budget-authoritative during run`

#### Scenario: Native usage adapter label
- **WHEN** Worker Setup renders an adapter verified with `native_usage` tracking mode
- **THEN** it shows `Tracking: Tracked via Native Usage`
- **AND** it shows `Runtime request guardrails: Not available`
- **AND** it shows `Accounting: Budget-authoritative after run`

#### Scenario: Observed-only adapter label
- **WHEN** Worker Setup renders an adapter with `observed_only` tracking mode
- **THEN** it shows `Tracking: Observed Only`
- **AND** it shows `Runtime request guardrails: Not available`
- **AND** it shows `Accounting: Not budget-authoritative`
- **AND** it does not show a Launch-ready badge

### Requirement: Observed-only diagnostics stay outside task launch
The Workers settings page MAY provide a diagnostic action for observed-only adapters, but that action SHALL NOT create or mutate AGILE Board task state.

#### Scenario: Observed-only diagnostic captures command evidence
- **WHEN** the operator runs a Worker Setup diagnostic for an observed-only adapter
- **THEN** the diagnostic records command start evidence, stdout/stderr, exit code or timeout, detected model when available, and a not-budget-authoritative warning
- **AND** no Task moves to Running, Review, Done, or Blocked because of the diagnostic

#### Scenario: Diagnostic does not imply launch readiness
- **WHEN** an observed-only diagnostic succeeds
- **THEN** Worker Setup continues to show the adapter as not launch-ready for governed Tasks
- **AND** the normal AGILE Board remains unable to launch Tasks with that adapter
