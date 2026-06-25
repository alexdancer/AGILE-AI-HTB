## MODIFIED Requirements

### Requirement: Project overview links to existing workflows
The project overview SHALL link to portal workflows in the context of the selected project when that workflow is project-scoped. Global settings and governance workflows SHALL remain reachable without duplicating their controls on the overview.

#### Scenario: Existing workflow links are available
- **WHEN** an authenticated operator opens a project overview
- **THEN** the overview SHALL link to the selected project's task board at `/projects/{project_id}/board`
- **AND** the overview SHALL link to the existing sessions list, Worker adapter settings, and project settings pages
