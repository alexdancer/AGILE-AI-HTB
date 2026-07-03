## ADDED Requirements

### Requirement: No-auth local entry uses project workspace landing
The project workspace entry flow SHALL route no-auth local operators to the same project landing used after successful login.

#### Scenario: No-auth root redirects to most recent project
- **WHEN** portal auth is not required
- **AND** at least one connected project exists
- **THEN** `GET /` SHALL redirect to `/projects/{project_id}` for the most recently updated connected project

#### Scenario: No-auth root redirects to project list without projects
- **WHEN** portal auth is not required
- **AND** no connected projects exist
- **THEN** `GET /` SHALL redirect to `/projects`
