## ADDED Requirements

### Requirement: Live Worker Run events are served through a bounded incremental projection

The portal SHALL expose live Worker Run timeline events to authenticated operators through a bounded
projection that returns only allowlisted event fields with capped lengths and counts, and that
supports incremental fetch by cursor so a client can retrieve only events newer than the last seen.

#### Scenario: Incremental fetch returns only newer events

- **WHEN** a client requests Worker Run events with a last-seen cursor
- **THEN** the projection returns only events after that cursor, in chronological order

#### Scenario: Projection is bounded and allowlisted

- **WHEN** Worker Run events are projected for the portal
- **THEN** each event exposes only allowlisted fields (such as created-at, id, kind, layer, title, bounded detail summary)
- **AND** text fields are length-capped and the number of events per response is bounded

#### Scenario: Access requires authentication

- **WHEN** an unauthenticated request asks for Worker Run events
- **THEN** the request is rejected
