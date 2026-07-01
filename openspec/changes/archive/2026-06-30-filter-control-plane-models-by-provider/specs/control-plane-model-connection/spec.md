## MODIFIED Requirements

### Requirement: Control-plane preset selection
The system SHALL provide a small set of portal presets and a real model dropdown for common control-plane connection shapes while preserving an explicit custom model path for OpenAI-compatible endpoints, future model IDs, existing non-curated saved IDs, and provider-incompatible saved IDs.

#### Scenario: OpenAI preset selected
- **WHEN** the operator selects the OpenAI preset
- **THEN** the form SHALL set provider `openai` and model `gpt-5.4-mini`
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
- **THEN** the model dropdown SHALL show OpenAI curated model choices
- **AND** it SHALL NOT show Anthropic `claude-*` curated choices as selectable options

#### Scenario: Anthropic provider filters model choices
- **WHEN** the operator selects provider `anthropic`
- **THEN** the model dropdown SHALL show Anthropic `claude-*` curated model choices
- **AND** it SHALL NOT show OpenAI curated choices as selectable options

#### Scenario: OpenAI-compatible provider uses custom model path
- **WHEN** the operator selects provider `openai-compatible`
- **THEN** the model dropdown SHALL select or expose the Custom model path
- **AND** first-party OpenAI and Anthropic curated model choices SHALL NOT be selectable for that provider

#### Scenario: Existing custom model preserved
- **WHEN** the saved Control Plane model is not one of the curated dropdown choices for the saved provider
- **THEN** the form SHALL preserve the existing model value through an explicit custom model path
- **AND** saving without choosing a different model SHALL NOT silently replace the custom value with a curated default
