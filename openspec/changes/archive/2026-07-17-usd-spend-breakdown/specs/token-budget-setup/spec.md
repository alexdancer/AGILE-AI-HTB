## ADDED Requirements

### Requirement: Budget spend breakdown includes coverage-aware USD cost

The dashboard budget spend breakdown SHALL present the actual USD cost of governed spend
alongside the existing per-category token counts, derived from the resolved per-turn cost already
recorded in the token ledger. The USD dimension SHALL be coverage-aware: it SHALL sum only
resolved (known) costs and SHALL distinguish spend whose cost is unknown from spend that is
genuinely free, so it never presents a fabricated zero. This dimension is informational; the
daily and per-session **token** budgets remain the sole enforcement authority and SHALL be
unchanged.

#### Scenario: USD cost is shown per category and in total

- **WHEN** the dashboard renders the budget spend breakdown and one or more turns have a resolved cost
- **THEN** the breakdown SHALL show a USD cost for each spend category derived from the sum of its turns' resolved costs
- **AND** it SHALL show a total USD cost across categories
- **AND** the token counts per category SHALL remain unchanged

#### Scenario: Unpriced spend is labeled, never shown as $0.00

- **WHEN** a spend category has tokens but none of its turns has a resolved cost
- **THEN** the breakdown SHALL present that category's cost as unavailable/unpriced
- **AND** it SHALL NOT present `$0.00` as if the spend were free

#### Scenario: Coverage is reported

- **WHEN** the dashboard renders the USD spend breakdown
- **THEN** it SHALL report how much of the tracked token spend is priced versus unpriced
- **AND** the coverage SHALL be derived from the token totals of turns with a resolved cost versus turns without one

#### Scenario: Enforcement stays token-based

- **WHEN** the USD spend breakdown is displayed
- **THEN** the daily budget zone and Worker launch budget checks SHALL continue to be computed from normalized governed token spend
- **AND** no USD value SHALL act as a spending cap or alter launch guardrails
