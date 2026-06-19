# Plan: Project Scaffold And Tooling

## Track

`track-001-project-scaffold`

## Status

`done`

## Implementation Phases

## Phase 1: Project Files And Dependency Configuration

- [x] Create base package directories under `app/`.
- [x] Add package marker files where needed.
- [x] Create `pyproject.toml`.
- [x] Add runtime dependencies.
- [x] Add development and test dependencies.
- [x] Add basic tool configuration for Pytest.

## Phase 2: FastAPI Application Skeleton

- [x] Create `app/main.py`.
- [x] Create a FastAPI application factory or module-level app.
- [x] Add app title and version from settings.
- [x] Add public `GET /health` endpoint.
- [x] Keep business routes out of this track.

## Phase 3: Configuration Layer

- [x] Create `app/core/config.py`.
- [x] Define typed settings for app, PostgreSQL, and JWT configuration.
- [x] Support environment variable loading.
- [x] Add `.env.example` with non-secret local example values.

## Phase 4: Database Infrastructure

- [x] Create `app/db/base.py` for SQLAlchemy declarative base.
- [x] Create `app/db/session.py` for SQL engine/session setup.
- [x] Keep database infrastructure PostgreSQL-only.
- [x] Avoid business models in this phase.

## Phase 5: Alembic Foundation

- [x] Initialize Alembic files.
- [x] Configure Alembic to read database URL from project settings or environment.
- [x] Connect Alembic metadata to SQLAlchemy base.
- [x] Do not create any schema migration yet.

## Phase 6: Docker Development Runtime

- [x] Create `Dockerfile` for the API service.
- [x] Create `docker-compose.yml`.
- [x] Add API service.
- [x] Add SQL database service.
- [x] Keep Docker Compose PostgreSQL-only.
- [x] Add local volumes for database persistence.
- [x] Ensure the API command starts Uvicorn in development mode.

## Phase 7: Smoke Tests

- [x] Create `tests/` structure.
- [x] Add app import smoke test.
- [x] Add health endpoint test.
- [x] Confirm Pytest can run locally.

## Phase 8: Verification And Context Sync

- [x] Run the smoke test suite.
- [x] Confirm app imports successfully.
- [x] Confirm `GET /health` works.
- [x] Confirm Docker Compose configuration is syntactically valid if Docker is available.
- [x] Update this plan with completed tasks.
- [x] Update `conductor/tracks.md` status after implementation and verification.

## Test Strategy

Minimum tests for this track:

- Import test for `app.main:app`.
- API test for `GET /health`.

Future tracks will add database, authentication, authorization, and workflow tests.

## Verification Commands

Recommended commands after implementation:

```text
python -m pytest
```

```text
python -m uvicorn app.main:app --reload
```

```text
docker compose config
```

```text
docker compose up --build
```

Use the Docker commands only when Docker is available on the development machine.

PostgreSQL can be inspected with DBeaver Community using the credentials in `.env.example`.

## Rollback Notes

This track should be safe to roll back by removing scaffold files because it creates no business data and no database migrations.

Files expected to be created during implementation:

```text
app/
alembic/
tests/
pyproject.toml
Dockerfile
docker-compose.yml
.env.example
```

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Dependency versions conflict | Keep dependencies minimal and common for FastAPI projects. |
| Alembic setup becomes coupled to future models too early | Configure metadata only; do not add business models or migrations. |
| Docker setup hides local configuration issues | Keep `.env.example` explicit and simple. |
| Scope expands into auth or domain models | Enforce non-goals and stop at health endpoint plus infrastructure. |

## Definition Of Done

- [x] Spec and plan are approved.
- [x] Scaffold files are implemented.
- [x] Smoke tests pass.
- [x] No domain models, migrations, or workflow endpoints are introduced.
- [x] Track status is updated in `conductor/tracks.md`.
