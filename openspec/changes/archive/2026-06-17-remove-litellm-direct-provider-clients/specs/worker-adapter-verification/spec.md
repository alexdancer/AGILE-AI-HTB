## MODIFIED Requirements

### Requirement: Provider keys remain separated from Worker Harness native config
The system SHALL keep AGILE-AI-HTB control-plane provider credentials separate from Worker Harness native credentials, SHALL only inject Harness Proxy credentials into Workers for proxy-governed tracking mode, and SHALL NOT expose real upstream provider API keys to Worker Adapter processes unless explicitly required by that Worker Harness's native configuration outside AGILE-AI-HTB.

#### Scenario: Proxy-governed Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter in proxy-governed mode
- **THEN** the Worker environment contains the Harness Proxy base URL and session-scoped Harness key but not the real control-plane provider API key

#### Scenario: Native Worker launch environment
- **WHEN** the system launches or verifies a Worker Adapter in native usage mode
- **THEN** the Worker uses its native harness configuration and the system does not require a control-plane provider key as Worker Harness auth

#### Scenario: Direct provider clients used upstream
- **WHEN** a proxy-governed Worker call reaches AGILE-AI-HTB's Harness Proxy
- **THEN** AGILE-AI-HTB forwards the governed request upstream through its configured direct provider client without passing the upstream provider key to the Worker Adapter process
