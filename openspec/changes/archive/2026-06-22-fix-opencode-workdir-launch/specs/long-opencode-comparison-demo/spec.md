## ADDED Requirements

### Requirement: Harness comparison writes to harness target
The long OpenCode comparison demo SHALL prove that harness-launched Worker changes land in `.demo/opencode-comparison/harness-target` and remain isolated from the direct baseline target and repository root.

#### Scenario: Harness target receives generated project
- **WHEN** the long OpenCode comparison task is launched through AGILE-AI-HTB with the OpenCode Worker Adapter configured to `.demo/opencode-comparison/harness-target`
- **THEN** generated project files such as `pyproject.toml`, `README.md`, `src/incident_ledger/`, `tests/`, and `examples/` appear under `.demo/opencode-comparison/harness-target`
- **AND** the evidence does not rely on files under repository-level `incident-ledger/` as the harness result

#### Scenario: Demo detects misplaced harness output
- **WHEN** OpenCode native usage evidence exists but generated files appear outside `.demo/opencode-comparison/harness-target`
- **THEN** the demo evidence SHALL identify this as a workdir mismatch
- **AND** the runbook SHALL direct the operator to treat it as a launch configuration failure, not as a successful harness comparison
