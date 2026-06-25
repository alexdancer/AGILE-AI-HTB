## ADDED Requirements

### Requirement: Repo Context Brief is built for connected project launches
The system SHALL build a bounded Repo Context Brief before launching a Worker Run for a connected project.

#### Scenario: Connected project launch builds brief
- **WHEN** an operator launches a task for a connected project
- **THEN** the system builds a Repo Context Brief before the Worker Adapter command starts
- **AND** the brief includes detected repo instructions, manifests, language/framework hints, test/run commands, and likely entry points when available

### Requirement: Repo Context Brief prefers existing repo instructions
The Repo Context Brief SHALL prioritize project-provided instructions and manifests over generic assumptions.

#### Scenario: Repo has AGENTS instructions
- **WHEN** the connected project contains AGENTS.md or another supported repo instruction file
- **THEN** the brief includes that file as a source
- **AND** the Worker prompt tells the Worker to follow those repo instructions before editing

### Requirement: Repo Context Brief is stored as evidence
The system SHALL store the Repo Context Brief and its source list with the Worker Run.

#### Scenario: Operator audits repo context
- **WHEN** an operator reviews a Worker Run after launch
- **THEN** the Worker Run evidence shows the Repo Context Brief or a bounded summary
- **AND** the evidence lists which repo files or signals were used to build it

### Requirement: Repo Context Brief is bounded
The system SHALL cap Repo Context Brief content before storing or injecting it into a Worker prompt.

#### Scenario: Large README is present
- **WHEN** a connected project contains large documentation or manifest files
- **THEN** the system includes bounded excerpts or summaries instead of unbounded full file contents
- **AND** the Worker prompt remains within configured launch prompt limits
