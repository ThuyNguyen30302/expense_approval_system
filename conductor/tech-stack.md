# Tech Stack

## Runtime

- Python
- FastAPI
- Uvicorn for local ASGI serving

## API And Validation

- FastAPI for routing, dependency injection, and OpenAPI documentation.
- Pydantic for request validation, response models, and settings.

## Persistence

- SQLAlchemy for relational data modeling and database access.
- Alembic for SQL database migrations.
- PostgreSQL JSON/JSONB for flexible metadata where useful.

## Authentication

- JWT access tokens.
- Secure password hashing.
- Role-based authorization.

## Testing

- Pytest for unit and integration tests.
- FastAPI test client for API endpoint tests.
- Database fixtures for isolated test data.

## Packaging And Tooling

Preferred setup:

- `pyproject.toml` for dependencies and tooling configuration.
- Dockerfile for the API service.
- Docker Compose for API and PostgreSQL services.

## Architectural Preference

Use a layered backend architecture:

- API routes
- Schemas
- Services
- Repositories
- SQLAlchemy models
- Core infrastructure

Routes should stay thin. Business logic belongs in services. Database access belongs in repositories or clearly scoped data-access helpers.

## Database Responsibility

PostgreSQL is the authoritative storage for:

- Users
- Expense requests
- Approval records
- Payment records
- Audit logs
- Receipt metadata
- Raw import payloads
- Extended event context

Use relational tables for core workflow data. Use JSON/JSONB columns only for metadata that does not need frequent relational filtering.
