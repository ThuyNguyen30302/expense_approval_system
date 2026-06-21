# Spec: Authentication And User Management

## Track

`track-002-auth-users`

## Status

`verified`

## Problem Statement

The project has a working FastAPI scaffold, configuration layer, SQLAlchemy session setup, Alembic foundation, Docker runtime, and health smoke tests. It does not yet have persistent users, authentication, JWT token issuing, authorization dependencies, or user management endpoints.

Future expense workflow tracks require a reliable identity layer before they can enforce requester ownership, manager visibility, accountant access, and admin privileges. This track creates that identity and access-control foundation without implementing expense workflows.

## Goals

- Add a persistent `users` table and SQLAlchemy model.
- Add Alembic migration support for the user schema.
- Store user passwords as secure hashes only.
- Normalize user emails before persistence and login lookup.
- Implement JWT access token creation and validation.
- Add FastAPI dependencies for current authenticated user and role checks.
- Add authentication endpoints for registration, login, and current-user profile.
- Add admin user management endpoints for creating, listing, reading, updating, and deactivating users.
- Add a repeatable development/demo bootstrap path for creating the first admin user.
- Add schemas, repositories, and services that follow the documented architecture.
- Add API and service tests for auth success paths, permission failures, duplicate emails, inactive users, and protected endpoint behavior.
- Keep response bodies free of password hashes and secrets.

## Non-Goals

- Do not implement expense, approval, payment, receipt, or audit workflow models.
- Do not implement refresh tokens or token rotation.
- Do not implement password reset, email verification, invitation flows, or notification delivery.
- Do not implement OAuth, SSO, MFA, or external identity providers.
- Do not seed production users or commit real secrets.
- Do not build a frontend.
- Do not add multi-tenant company isolation.

## Users Affected

- Employees who need to register, log in, and access their own profile.
- Admins who need to manage users and roles.
- Developers implementing later workflow tracks that require current-user and role dependencies.
- Reviewers evaluating security, authorization boundaries, and API consistency.

## Functional Requirements

### User Model

Create a `users` table aligned with `database-schema.md`.

Required fields:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `role`
- `manager_id`
- `department`
- `is_active`
- `created_at`
- `updated_at`
- `deactivated_at`

Required behavior:

- User IDs should be UUIDs.
- Emails should be stored normalized lowercase.
- Email must be unique.
- Password hashes must never be returned by API responses.
- Supported roles are `employee`, `manager`, `accountant`, and `admin`.
- `manager_id` may reference another user.
- Users should be deactivated rather than physically deleted.

### Authentication

Implement password-based login.

Required behavior:

- Verify submitted email and password against the stored password hash.
- Return generic authentication errors for invalid email, invalid password, inactive user, malformed token, expired token, or missing authenticated user.
- Issue JWT access tokens with an expiration.
- Include enough claims to load and authorize the user, at minimum user ID, role, token type, and expiration.
- Read JWT secret, algorithm, and expiration settings from configuration.

### Registration

Expose demo-friendly registration as described in `api-design.md`.

Required behavior:

- `POST /api/v1/auth/register` creates an active `employee` user by default.
- Registration accepts `email`, `password`, and `full_name`.
- Registration rejects duplicate emails.
- Registration returns the public user response shape.
- Registration must not allow clients to self-assign elevated roles.

### Development Admin Bootstrap

Provide a documented CLI command or seed script that creates the first admin for development/demo usage.

Required behavior:

- The command is repeatable.
- The command creates an admin user when the email does not exist.
- The command updates, reactivates, and promotes the user when the email already exists.
- The command refuses to run when `APP_ENV=production`.
- Self-service registration remains employee-only.

### Current User

Expose the current authenticated user endpoint.

Required behavior:

- `GET /api/v1/auth/me` requires a valid bearer token.
- The endpoint returns the current active user's public profile.
- Inactive users cannot authenticate through this endpoint.

### Admin User Management

Expose admin-only user management endpoints.

Required behavior:

- `GET /api/v1/users` lists users with pagination.
- `GET /api/v1/users` supports optional filtering by `role` and `is_active`.
- `POST /api/v1/users` creates a user with an explicit role.
- `GET /api/v1/users/{user_id}` returns a user for admins.
- `GET /api/v1/users/{user_id}` may also allow a user to access their own record.
- `PATCH /api/v1/users/{user_id}` updates allowed admin-editable fields.
- `POST /api/v1/users/{user_id}/deactivate` deactivates a user and sets `deactivated_at`.
- Non-admin users must receive `403 Forbidden` for admin-only operations.

Allowed admin-editable fields should include:

- `email`
- `full_name`
- `role`
- `manager_id`
- `department`
- `is_active`
- `password`

Implementation should treat password changes carefully by hashing new passwords before storage.

### Authorization Dependencies

Add reusable API dependencies.

Required dependencies:

- Database session dependency, using the existing session infrastructure.
- Current active user dependency.
- Role-check dependency for one or more allowed roles.
- Admin-only dependency.

These dependencies should be usable by later expense workflow tracks.

### Error Handling

Auth and user endpoints should use consistent application-level error responses where practical.

Expected cases:

- `400 Bad Request` for invalid user management input beyond schema validation.
- `401 Unauthorized` for missing or invalid authentication.
- `403 Forbidden` for authenticated users without permission.
- `404 Not Found` for missing users that the requester is allowed to know about.
- `409 Conflict` for duplicate email conflicts.
- `422 Unprocessable Entity` for Pydantic validation errors.

## API Behavior

Base path:

```text
/api/v1
```

### Register User

```text
POST /api/v1/auth/register
```

Request:

```json
{
  "email": "employee@example.com",
  "password": "strong-password",
  "full_name": "Employee User"
}
```

Response:

```json
{
  "id": "user-id",
  "email": "employee@example.com",
  "full_name": "Employee User",
  "role": "employee",
  "is_active": true,
  "created_at": "2026-06-19T05:00:00Z"
}
```

### Login

```text
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "employee@example.com",
  "password": "strong-password"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Get Current User

```text
GET /api/v1/auth/me
```

Response:

```json
{
  "id": "user-id",
  "email": "employee@example.com",
  "full_name": "Employee User",
  "role": "employee",
  "is_active": true
}
```

### List Users

```text
GET /api/v1/users
```

Required role: `admin`

Query parameters:

- `role`
- `is_active`
- `limit`
- `offset`

Response should use the shared paginated response shape.

### Create User

```text
POST /api/v1/users
```

Required role: `admin`

Request:

```json
{
  "email": "manager@example.com",
  "password": "strong-password",
  "full_name": "Manager User",
  "role": "manager",
  "is_active": true,
  "manager_id": null,
  "department": "Sales"
}
```

### Get User

```text
GET /api/v1/users/{user_id}
```

Required role: `admin`, or current user accessing themself.

### Update User

```text
PATCH /api/v1/users/{user_id}
```

Required role: `admin`

### Deactivate User

```text
POST /api/v1/users/{user_id}/deactivate
```

Required role: `admin`

## Data Model Implications

Add the first business table:

```text
users
```

Migration should include:

- UUID primary key.
- Unique email constraint or unique index.
- Role constraint for supported role values.
- `manager_id` self-reference with `ON DELETE SET NULL`.
- `manager_id != id` check.
- Useful indexes for role, manager, department, and active status.
- UTC-aware timestamp columns.

No expense-related tables should be added in this track.

## Authorization Rules

- Registration is public and always creates an `employee` role.
- Login is public but only succeeds for active users.
- `GET /api/v1/auth/me` requires a valid token and active user.
- Admin user management requires `admin`.
- A user may read their own user record if the endpoint is designed to allow self-access.
- Non-admin users may not list, create, update, deactivate, or assign roles.
- Inactive users should not be treated as authenticated active users.

## Acceptance Criteria

- Track has SQLAlchemy user model, schemas, repository, services, security helpers, dependencies, routes, and migration in the implementation phase.
- `POST /api/v1/auth/register` creates an employee user and returns no password hash.
- `POST /api/v1/auth/login` returns a bearer access token for valid active credentials.
- `GET /api/v1/auth/me` returns the authenticated active user.
- Admin can create, list, read, update, and deactivate users.
- Non-admin users cannot access admin-only user management endpoints.
- Duplicate emails are rejected consistently.
- Passwords are stored only as hashes.
- JWT configuration comes from settings.
- Tests cover auth success, auth failure, role boundaries, duplicate email, inactive user behavior, and public response shapes.
- Existing health tests continue to pass.

## Open Decisions

- Resolved: include a development/demo CLI command for repeatable first-admin bootstrap.
- Decide whether `GET /api/v1/users/{user_id}` should return `404` or `403` when a non-admin requests another user's record. Recommended default: `403` because the resource type is not sensitive in this portfolio API, but hidden-resource behavior can be adopted later.
- Decide whether admin `PATCH /api/v1/users/{user_id}` should allow reactivation by setting `is_active=true`. Recommended default: allow it and clear `deactivated_at`.
- Decide whether to use database-native UUID generation or application-generated UUIDs. Recommended default: application-generated UUIDs for simple local setup without PostgreSQL extensions.
