# Spec: Project Scaffold And Tooling

## Track

`track-001-project-scaffold`

## Status

`approved`

## Problem Statement

The project currently has strong context documents but no executable backend foundation. Future feature work needs a clean FastAPI project scaffold, dependency setup, Docker runtime, database connection structure, Alembic migration foundation, and Pytest configuration.

This track creates the implementation foundation while avoiding business feature implementation.

## Goals

- Create the initial Python backend project structure described in `backend-architecture.md`.
- Configure project dependencies for FastAPI, SQLAlchemy, Alembic, Pydantic, JWT support, Pytest, and Docker-based local development.
- Add application configuration loading from environment variables.
- Add PostgreSQL database connection modules without creating domain models yet.
- Initialize Alembic structure without writing schema migrations.
- Add test setup and at least one minimal smoke test for the application.
- Add a minimal health endpoint to prove the app boots.
- Add Dockerfile and Docker Compose services for API and PostgreSQL.
- Add `.env.example` documenting required local environment variables.

## Non-Goals

- Do not implement authentication behavior.
- Do not implement user, expense, approval, payment, or audit models.
- Do not create Alembic migrations for business tables.
- Do not implement domain workflow endpoints.
- Do not implement JWT token issuing or password hashing flows beyond dependency availability.
- Do not seed real application data.
- Do not build any frontend.

## Users Affected

- Developer maintaining and extending the backend.
- Reviewer evaluating project structure and development workflow.
- Future implementation tracks that depend on stable project layout.

## Functional Requirements

### Project Structure

Create the intended directory layout:

```text
app/
  api/
    routes/
  core/
  db/
  models/
  schemas/
  repositories/
  services/
  main.py
alembic/
tests/
```

The scaffold may include empty package marker files where needed.

### Application Entrypoint

The FastAPI app should:

- Be created in `app/main.py`.
- Use project title and version from configuration.
- Register a health route.
- Be importable by Uvicorn as `app.main:app`.

### Health Endpoint

Add a minimal endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

This endpoint is only for scaffold verification.

### Configuration

Add typed settings for:

- app environment
- debug flag
- app title
- app version
- SQL database URL
- JWT secret key
- JWT algorithm
- access token expiry minutes

Settings should read from environment variables and support local development through `.env`.

### SQL Database Setup

Add SQLAlchemy infrastructure for:

- Engine creation.
- Session factory.
- Declarative base.
- Dependency-compatible session access for future routes.

No business models should be created in this track.

### Alembic Setup

Add Alembic configuration and environment files.

Alembic should be ready to detect SQLAlchemy metadata in a future track, but this track must not create schema migrations for business tables.

### Dependency Management

Use `pyproject.toml` as the dependency and tooling configuration file.

Dependencies should cover:

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- Pydantic settings support
- JWT/password hashing libraries needed by later auth track
- Pytest and HTTP test client support

### Docker Setup

Add:

- `Dockerfile` for the API.
- `docker-compose.yml` with services for API and PostgreSQL.
- Persistent volumes for local database services.

The API service should be able to start the FastAPI app in development mode.

### Test Setup

Add Pytest configuration and smoke tests.

Minimum required tests:

- App import succeeds.
- `GET /health` returns `200`.
- `GET /health` returns `{"status": "ok"}`.

## API Behavior

Only this endpoint is introduced:

```text
GET /health
```

No `/api/v1` business endpoints are introduced in this track.

## Data Model Implications

- No business tables are added.
- No Alembic migration is created.
- SQLAlchemy base metadata is prepared for future model registration.
- PostgreSQL setup is prepared for future relational models and JSONB metadata.

## Authorization Rules

- `GET /health` is public.
- No authenticated or role-protected endpoints are implemented in this track.

## Acceptance Criteria

- Project contains a clear FastAPI scaffold matching the documented architecture.
- `app.main:app` can be imported.
- Local app can be started with Uvicorn.
- `GET /health` returns the expected response.
- Pytest can run the smoke test suite successfully.
- Docker Compose defines API and PostgreSQL services.
- Alembic is initialized and ready for later migrations.
- `.env.example` documents required environment variables.
- No business workflow code or database schema migrations are created.

## Open Decisions

- Choose the SQL database image for Docker Compose. Recommended default: PostgreSQL.
- Choose package management command style. Recommended default: standard `pip` install from `pyproject.toml` for broad familiarity.
