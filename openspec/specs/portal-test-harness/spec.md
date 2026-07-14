# portal-test-harness Specification

## Purpose

Define how Portal tests share repeated setup behavior through a test-only helper Module while preserving production behavior and the existing pytest execution model.

## Requirements

### Requirement: Shared Portal test setup Interface
The Portal test suite SHALL provide one shared test helper Module for repeated Portal setup behavior, including authenticated test client construction, fake Control Plane LLM responses, Portal auth headers, Connected Project creation, and project task metadata helpers.

#### Scenario: Portal tests use shared setup helpers
- **WHEN** a Portal test needs an authenticated client, fake Control Plane LLM, Connected Project, or project task metadata
- **THEN** the test imports that setup behavior from the shared Portal test helper Module instead of defining a local duplicate helper block

#### Scenario: Helper extraction preserves Portal test behavior
- **WHEN** the shared helper Module replaces duplicated helper definitions in the Portal test modules
- **THEN** the existing Portal tests pass without changing their production behavior assertions

### Requirement: Portal test harness extraction remains test-only
The Portal test harness extraction MUST NOT change production Portal routes, templates, database schema, Worker Adapter behavior, Control Plane behavior, Orchestration Board behavior, or public APIs.

#### Scenario: Production code remains untouched
- **WHEN** the Portal test harness Module is implemented
- **THEN** implementation changes are limited to Portal test files and the shared Portal test helper Module

### Requirement: Pytest machinery remains unchanged
The Portal test harness extraction MUST preserve the repository's existing pytest discovery and execution model.

#### Scenario: No extra pytest framework layer
- **WHEN** the shared Portal test helper Module is added
- **THEN** the change does not add `conftest.py`, pytest fixtures, custom markers, plugins, or pytest configuration for this extraction
