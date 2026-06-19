# Backend Architecture

## Architecture Overview

The backend will be a FastAPI application organized around clear application layers:

- API layer for routes, request parsing, response models, and dependency injection.
- Service layer for business rules and workflow decisions.
- Repository layer for database access.
- Domain models for persistent entities and status concepts.
- Security layer for authentication, password hashing, JWT handling, and role checks.
- Infrastructure layer for configuration, database sessions, logging, and Docker runtime concerns.

The application should keep business logic out of route handlers. Routes should validate input, call services, and return response schemas.

## Proposed Project Structure

```text
app/
  api/
    deps.py
    routes/
      auth.py
      users.py
      expenses.py
      approvals.py
      payments.py
  core/
    config.py
    security.py
    errors.py
  db/
    session.py
    base.py
  models/
    user.py
    expense.py
    approval.py
    payment.py
    audit_log.py
  schemas/
    auth.py
    user.py
    expense.py
    approval.py
    payment.py
    common.py
  repositories/
    users.py
    expenses.py
    audit_logs.py
  services/
    auth.py
    users.py
    expenses.py
    approvals.py
    payments.py
  main.py
alembic/
tests/
docker-compose.yml
Dockerfile
pyproject.toml
```

This structure is a target guideline, not code to implement immediately.

## Technology Responsibilities

### FastAPI

- Application entrypoint.
- Route registration.
- Dependency injection.
- Request and response validation.
- OpenAPI documentation.

### Pydantic

- Request schemas.
- Response schemas.
- Shared validation rules.
- Settings model for environment configuration.

### SQLAlchemy

- Main relational persistence layer.
- ORM models for users, expenses, approval decisions, payments, and audit history.
- Transaction management.

### Alembic

- Database schema migrations.
- Versioned changes for SQLAlchemy-backed tables.

### JWT Authentication

- Access token-based authentication.
- Tokens should include user ID, role, token type, and expiration.
- Token validation should happen through FastAPI dependencies.

### Pytest

- Unit and integration testing.
- API workflow tests with FastAPI test client.
- Database test fixtures.

### Docker

- Local development environment.
- Services for API, PostgreSQL, and optionally test database.

## Persistence Model

### PostgreSQL Database

Core transactional data should live in PostgreSQL:

- users
- expenses
- approval decisions
- payment records
- audit logs
- receipt metadata
- flexible event metadata through JSON/JSONB columns

PostgreSQL is preferred because expense approvals require consistent transitions, joins, constraints, transactional updates, and easy inspection through tools like DBeaver.

Use JSON/JSONB columns for flexible metadata when the data does not justify a separate normalized table.

## Layer Responsibilities

### API Routes

Routes should:

- Declare paths and HTTP methods.
- Accept Pydantic request schemas.
- Use dependencies for authentication, database sessions, and authorization.
- Call service functions.
- Return Pydantic response schemas.

Routes should not:

- Implement status transition rules.
- Build SQL queries directly unless the endpoint is trivial.
- Hash passwords or create JWTs directly.

### Services

Services should:

- Enforce business rules.
- Validate workflow transitions.
- Coordinate multiple repositories.
- Create audit history entries.
- Manage transactional operations.

Services should be the main place for rules such as:

- Only submitted expenses can be manager-approved.
- Rejections require a reason.
- Paid expenses cannot be modified.
- Employees can only see their own expenses unless they have elevated roles.

### Repositories

Repositories should:

- Encapsulate database queries.
- Return ORM entities or simple data objects to services.
- Keep persistence details out of services where practical.

### Schemas

Schemas should:

- Define API input and output contracts.
- Avoid leaking internal fields such as password hashes.
- Use separate create, update, and response models.

## Configuration

Configuration should come from environment variables and be represented through a typed settings object.

Expected settings:

- application environment
- debug flag
- API title/version
- SQL database URL
- JWT secret key
- JWT algorithm
- access token expiry minutes
- password hashing settings
- CORS origins if needed

Secrets must not be committed to source control.

## Authentication Flow

1. User submits email and password.
2. Auth service verifies credentials against stored password hash.
3. Auth service creates JWT access token.
4. Client sends token in `Authorization: Bearer <token>`.
5. Dependency validates token and loads current user.
6. Role dependencies enforce endpoint permissions.

## Authorization Model

Use role-based access control with optional ownership checks.

Role checks:

- Employee endpoints require authenticated users.
- Manager actions require `manager` or `admin`.
- Accountant actions require `accountant` or `admin`.
- Admin user management requires `admin`.

Ownership checks:

- Employees may access only their own expenses.
- Managers may access expenses assigned to them or within their team.
- Accountants may access approved expenses requiring review or payment.
- Admins may access all records.

## Transaction Boundaries

Status transitions should happen in a single SQL transaction:

1. Load expense.
2. Validate current status and actor permission.
3. Update expense status.
4. Insert approval/payment record if needed.
5. Insert audit log entry.
6. Commit.

If any step fails, the transaction should roll back.

## Error Handling

Use consistent application exceptions mapped to HTTP errors:

- `400 Bad Request` for invalid state transitions or invalid input beyond schema validation.
- `401 Unauthorized` for missing or invalid authentication.
- `403 Forbidden` for authenticated users without permission.
- `404 Not Found` for missing resources or hidden resources.
- `409 Conflict` for duplicate resources or conflicting workflow state.
- `422 Unprocessable Entity` for Pydantic validation errors.

## Testing Architecture

Recommended test categories:

- Unit tests for services.
- API tests for route behavior.
- Authorization tests for role boundaries.
- Workflow tests for expense status transitions.
- Repository tests for important query behavior.

Test fixtures should create isolated users, expenses, and database sessions.

## Deployment Shape

Initial Docker Compose services:

- API service running FastAPI.
- PostgreSQL database service.

Production deployment can later add:

- reverse proxy
- managed database services
- structured logging
- monitoring
- secret management
