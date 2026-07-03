# control-plane-model-connection Specification

## Purpose
Define the model connection AGILE-AI-HTB uses for its own control-plane work, separate from any Worker Harness model configuration or credentials.
## Requirements
### Requirement: Control-plane model connection
The system SHALL provide a distinct direct control-plane model connection for AGILE-AI-HTB's own orchestration work, separate from Worker Harness model access and without requiring LiteLLM.

#### Scenario: Control-plane model configured
- **WHEN** the operator configures a control-plane provider, model, and required credentials or endpoint
- **THEN** AGILE-AI-HTB uses that direct provider API connection for task estimation, planning, recommendation, summaries, and reports

#### Scenario: Control-plane model missing
- **WHEN** no valid control-plane model connection is configured
- **THEN** AGILE-AI-HTB keeps local board and manual task workflows available but marks model-powered estimation, planning, and reporting as unavailable with a clear setup reason

### Requirement: Control-plane setup language
The system SHALL describe the AGILE-AI-HTB model connection as the control-plane model in UI and documentation rather than presenting it as a Worker Harness provider key.

#### Scenario: User views model setup
- **WHEN** the User opens settings or local setup documentation
- **THEN** the system distinguishes AGILE-AI-HTB control-plane model setup from OpenCode, Claude Code, Codex, or other Worker Harness setup

### Requirement: Backward-compatible provider key aliases
The system SHALL preserve existing provider key environment aliases where practical while treating explicit control-plane model settings as the canonical configuration and SHALL NOT copy one control-plane key into unrelated provider-specific environment variables.

#### Scenario: Explicit control-plane key exists
- **WHEN** `AGILE_AI_HTB_CONTROL_API_KEY` is present
- **THEN** the system uses it only for the configured control-plane/upstream provider client

#### Scenario: Legacy provider key env exists
- **WHEN** a legacy provider key environment variable is present and explicit control-plane credentials are absent
- **THEN** the system may use the legacy value for the control-plane model and labels it as compatibility behavior rather than Worker Harness configuration

#### Scenario: Provider env fan-out avoided
- **WHEN** the application starts with a configured control-plane API key
- **THEN** the system does not copy that key into unrelated provider-specific env vars such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, or `GROQ_API_KEY`

### Requirement: Control-plane connection test
The system SHALL allow the operator to verify the configured control-plane model without launching a Worker Harness, and SHALL present browser-initiated test results inside the Control Plane settings UI rather than navigating to a raw JSON result page.

#### Scenario: Control-plane test succeeds
- **WHEN** the operator runs a control-plane model connection test
- **THEN** the system records success evidence without exposing credentials and enables model-powered control-plane actions

#### Scenario: Control-plane test fails
- **WHEN** the configured control-plane model cannot be called
- **THEN** the system records a sanitized failure reason and keeps Worker Harness launch readiness independent from the failed control-plane test

#### Scenario: Browser test returns to settings UI
- **WHEN** an authenticated operator submits the Control Plane connection test from the Portal settings page
- **THEN** the system SHALL record the sanitized test result
- **AND** the response SHALL return the operator to `/settings/control-plane` instead of rendering a JSON response page
- **AND** the settings page SHALL show a concise success or failure result for the latest test

#### Scenario: Settings UI preserves auditable raw evidence
- **WHEN** the Control Plane settings page displays a recorded connection test
- **THEN** the page SHALL show the primary result as readable status fields such as status, provider, model, token usage, or sanitized error
- **AND** full sanitized raw details SHALL remain available behind a native disclosure or equivalent secondary detail view
- **AND** raw control-plane API key values SHALL NOT be displayed

#### Scenario: API test remains JSON
- **WHEN** an authenticated API client posts a Control Plane connection test request that prefers JSON
- **THEN** the system SHALL return the machine-readable JSON result with the recorded sanitized status

### Requirement: Live control-plane connection editing
The system SHALL allow an authenticated operator to edit the control-plane provider, model, base URL, and API key environment variable name from the portal without restarting the application.

#### Scenario: Operator saves a new control-plane model
- **WHEN** the operator saves valid control-plane connection settings from the portal
- **THEN** the system persists the non-secret settings before changing runtime state
- **AND** subsequent control-plane requests use the new effective settings without requiring a server restart

#### Scenario: Config persistence fails
- **WHEN** the operator saves control-plane connection settings and the non-secret config file cannot be written
- **THEN** the system SHALL reject the save with a clear error
- **AND** the running control-plane settings SHALL remain unchanged

#### Scenario: Existing request is in flight
- **WHEN** a control-plane request is already in progress while the operator saves new settings
- **THEN** the system SHALL allow that in-flight request to finish using the settings it already started with
- **AND** new control-plane requests SHALL use the saved settings after the save succeeds

### Requirement: Control-plane preset selection
The system SHALL provide a small set of portal presets and a real model dropdown for common control-plane connection shapes while preserving an explicit custom model path for OpenAI-compatible endpoints, future model IDs, existing non-curated saved IDs, and provider-incompatible saved IDs.

#### Scenario: OpenAI preset selected
- **WHEN** the operator selects the OpenAI preset
- **THEN** the form SHALL set provider `openai` and model `gpt-5.4`
- **AND** it SHALL leave the default OpenAI base URL behavior unless the operator overrides it

#### Scenario: Anthropic preset selected
- **WHEN** the operator selects the Anthropic preset
- **THEN** the form SHALL set provider `anthropic` and model `claude-haiku-4-5`
- **AND** it SHALL leave the default Anthropic base URL behavior unless the operator overrides it

#### Scenario: OpenAI-compatible preset selected
- **WHEN** the operator selects the OpenAI-compatible preset
- **THEN** the form SHALL set provider `openai-compatible`
- **AND** it SHALL require or expose free-text model and base URL fields for the compatible provider

#### Scenario: Operator chooses a curated control-plane model
- **WHEN** the operator opens the Control Plane model settings form for a curated provider/model choice
- **THEN** the normal model chooser SHALL render as a native dropdown control rather than a textbox or `datalist`
- **AND** the dropdown SHALL include the supported curated Control Plane model choices for the selected provider

#### Scenario: OpenAI provider filters model choices
- **WHEN** the operator selects provider `openai`
- **THEN** the model dropdown SHALL show OpenAI curated model choices, including `gpt-5.4`
- **AND** it SHALL NOT show Anthropic `claude-*` curated choices as selectable options

#### Scenario: Anthropic provider filters model choices
- **WHEN** the operator selects provider `anthropic`
- **THEN** the model dropdown SHALL show Anthropic `claude-*` curated model choices, including `claude-sonnet-5`
- **AND** it SHALL NOT show OpenAI curated choices as selectable options

#### Scenario: OpenAI-compatible provider uses custom model path
- **WHEN** the operator selects provider `openai-compatible`
- **THEN** the model dropdown SHALL select or expose the Custom model path
- **AND** first-party OpenAI and Anthropic curated model choices SHALL NOT be selectable for that provider

#### Scenario: Existing custom model preserved
- **WHEN** the saved Control Plane model is not one of the curated dropdown choices for the saved provider
- **THEN** the form SHALL preserve the existing model value through an explicit custom model path
- **AND** saving without choosing a different model SHALL NOT silently replace the custom value with a curated default

### Requirement: Control-plane split-model default
The system SHALL default to applying the selected control-plane model to estimator and task-breakdown model settings while allowing the operator to preserve split-model settings.

#### Scenario: Default model coupling accepted
- **WHEN** the operator saves a control-plane model with the default coupling option enabled
- **THEN** the system SHALL persist the selected model as `control_plane_model`, `estimator_model`, and `task_breakdown_model`

#### Scenario: Split-model option preserved
- **WHEN** the operator saves a control-plane model with the coupling option disabled
- **THEN** the system SHALL persist the selected model as `control_plane_model`
- **AND** it SHALL preserve the existing `estimator_model` and `task_breakdown_model` values

### Requirement: Stale control-plane test status
The system SHALL mark previous control-plane connection test evidence as stale after saved control-plane connection settings change.

#### Scenario: Settings saved after previous successful test
- **WHEN** the operator saves changed control-plane connection settings after a prior successful connection test
- **THEN** the system SHALL display the control-plane setup state as needing a test
- **AND** it SHALL NOT present the previous test as proof that the new provider/model is reachable

#### Scenario: Operator tests changed settings
- **WHEN** the operator runs the control-plane connection test after changing settings
- **THEN** the system SHALL record sanitized success or failure evidence for the new effective provider/model

### Requirement: Configurable Task Breakdown Model
The system SHALL provide a separately configurable Task Breakdown Model for Task Breakdown Agent work in the control-plane/orchestrator model layer, distinct from the Estimator LLM and from Worker Adapter models.

#### Scenario: Task Breakdown Model configured
- **WHEN** the operator configures a Task Breakdown Model
- **THEN** AGILE-AI-HTB uses that model for semantic task breakdown and proposed vertical-slice review generation
- **AND** usage is recorded as `task_breakdown` Orchestration Tokens rather than Worker execution spend

#### Scenario: Task Breakdown Model not explicitly configured
- **WHEN** no explicit Task Breakdown Model is configured
- **THEN** the system uses a documented control-plane fallback model setting
- **AND** still labels the usage as Task Breakdown Agent/control-plane spend, not Worker Adapter spend

#### Scenario: Worker Adapter model remains separate
- **WHEN** the Task Breakdown Agent runs before estimation
- **THEN** the system does not use OpenCode, Claude Code, Codex, Hermes, or other Worker Adapter model configuration as the Task Breakdown Model unless explicitly configured as a control-plane model connection

### Requirement: Portal-managed control-plane API key entry
The system SHALL allow an authenticated operator to provide the control-plane API key value from the control-plane model settings portal without requiring manual environment variable export or manual `.htb/secrets.env` editing for the common local setup path.

#### Scenario: Operator saves a new control-plane key
- **WHEN** an authenticated operator enters provider/model settings and a non-empty control-plane API key value in the portal
- **THEN** the system SHALL store the key value in ignored local secret storage for the configured control-plane API key name
- **AND** the system SHALL NOT store the key value in `.htb/config.toml`
- **AND** subsequent control-plane requests SHALL be able to load the saved key without a server restart

#### Scenario: Operator leaves key blank
- **WHEN** an authenticated operator saves control-plane settings with the API key field blank
- **THEN** the system SHALL preserve any existing stored control-plane API key value
- **AND** the system SHALL NOT replace the stored value with an empty string or placeholder

#### Scenario: Portal redacts key values
- **WHEN** the control-plane settings page, save response, connection status, logs, or test evidence are rendered
- **THEN** the system SHALL show whether a key is present without displaying the raw control-plane API key value

#### Scenario: Connection test remains explicit
- **WHEN** an authenticated operator saves a new control-plane API key value
- **THEN** the system SHALL mark prior connection test evidence as needing a new test
- **AND** the system SHALL NOT require the provider connection test to pass before saving the local settings and secret

### Requirement: Provider-compatible Task Breakdown structured output
The system SHALL normalize provider-specific structured-output response wrappers for Task Breakdown Agent calls while preserving strict validation of the resulting Proposed Task Breakdown object.

#### Scenario: Claude returns fenced JSON for task breakdown
- **WHEN** the configured Task Breakdown Model is a direct Anthropic/Claude control-plane model
- **AND** the provider response content is a single fenced JSON block containing a complete Proposed Task Breakdown object
- **THEN** the system parses the fenced JSON content
- **AND** validates it with the existing Task Breakdown schema before creating a Proposed Task Breakdown review

#### Scenario: Claude task breakdown requires enough output tokens
- **WHEN** the Task Breakdown Agent calls a direct Anthropic/Claude control-plane model
- **THEN** the request includes an explicit completion-token cap of at least 16,384 tokens for the required Proposed Task Breakdown JSON object
- **AND** the cap is scoped to Task Breakdown Agent calls rather than changing unrelated control-plane requests

#### Scenario: Invalid or truncated provider output remains failed breakdown
- **WHEN** a Task Breakdown Model response is malformed, incomplete, truncated, or does not decode to an object that satisfies the Task Breakdown schema
- **THEN** the system records a breakdown-failed/manual recovery state
- **AND** it does not silently create deterministic Markdown-split tasks
- **AND** it does not create an oversized whole-source Estimated Task without operator action

#### Scenario: Worker model configuration remains separate
- **WHEN** stabilizing direct Anthropic/Claude Task Breakdown Agent parsing
- **THEN** the system does not change Worker Adapter model discovery, Worker launch commands, or Worker execution model selection

### Requirement: Task Breakdown request scale is explicit
The system SHALL keep Task Breakdown Model request sizing explicit and scoped to Task Breakdown Agent calls so operators can distinguish reachability checks from full structured breakdown generation.

#### Scenario: Task Breakdown uses explicit output budget
- **WHEN** the Task Breakdown Agent calls a configured Task Breakdown Model
- **THEN** the request SHALL use an explicit max output token budget scoped to Task Breakdown Agent work
- **AND** the output budget SHALL NOT change unrelated control-plane connection tests, task estimation requests, Worker Adapter launches, or Worker model selection

#### Scenario: Task Breakdown timeout is explicit
- **WHEN** the Task Breakdown Agent calls a configured Task Breakdown Model
- **THEN** the provider request timeout used for that call SHALL be explicit in configuration or code
- **AND** timeout diagnostics SHALL report that timeout value without exposing secrets or source text

#### Scenario: Reachability test remains small
- **WHEN** the operator runs the Control Plane connection test
- **THEN** the test SHALL remain a small provider reachability check
- **AND** the system SHALL NOT treat successful reachability evidence as proof that large Task Breakdown structured-output requests will complete within their timeout budget

