# Plan: Authentication And User Management

## Track

`track-002-auth-users`

## Status

`verified`

## Implementation Phases

## Phase 1: Context And Test Strategy

- [x] Re-read the relevant sections of `product-requirements.md`, `api-design.md`, `backend-architecture.md`, `coding-rules.md`, and `database-schema.md`.
- [x] Confirm the approved scope still excludes expenses, approvals, payments, receipts, audit logs, refresh tokens, and frontend work.
- [x] Decide how tests will create isolated users and database sessions.
- [x] Decide whether test database setup will use Alembic migrations, SQLAlchemy metadata, or explicit fixture setup.

## Phase 2: Domain Types And Persistence Model

- [x] Add stable role enum values for `employee`, `manager`, `accountant`, and `admin`.
- [x] Create the SQLAlchemy `User` model.
- [x] Add user fields from `database-schema.md`.
- [x] Add indexes and constraints for email uniqueness, role, manager, department, active status, and self-manager prevention.
- [x] Register the user model with SQLAlchemy metadata.
- [x] Add an Alembic migration for the `users` table.
- [x] Verify the migration is reversible where practical.

## Phase 3: Schemas And Shared Response Shapes

- [x] Add user create schema for public registration.
- [x] Add admin user create schema.
- [x] Add admin user update schema.
- [x] Add public user response schema.
- [x] Add login request schema.
- [x] Add token response schema.
- [x] Add pagination response schema or user-list-specific paginated schema.
- [x] Ensure schemas never expose `hashed_password`.
- [x] Add validation for emails, passwords, role values, optional manager IDs, and update payloads.

## Phase 4: Security Helpers

- [x] Create password hashing helper.
- [x] Create password verification helper.
- [x] Create JWT access token helper.
- [x] Create JWT decode/validation helper.
- [x] Ensure token claims include subject user ID, role, token type, and expiration.
- [x] Use settings for JWT secret, algorithm, and token expiration.
- [x] Return generic authentication failures for invalid credentials and invalid tokens.

## Phase 5: Repositories

- [x] Add user repository helpers for create, get by ID, get by email, list with filters, update, and deactivate.
- [x] Keep transaction commits outside low-level helpers unless intentionally owned by a service.
- [x] Normalize email before lookup and persistence.
- [x] Support pagination for user listing.
- [x] Support duplicate email detection.

## Phase 6: Services

- [x] Add auth service for registration, credential authentication, token creation, and current-user loading.
- [x] Add user service for admin create, list, read, update, deactivate, and self-read behavior.
- [x] Enforce duplicate email conflicts in service behavior.
- [x] Enforce inactive user authentication rules.
- [x] Hash passwords before persistence.
- [x] Keep route handlers thin.

## Phase 7: API Dependencies

- [x] Add database session dependency wiring under the API layer.
- [x] Add OAuth2 bearer token dependency or equivalent bearer-token parser.
- [x] Add current user dependency.
- [x] Add current active user dependency.
- [x] Add reusable role-check dependency.
- [x] Add admin-only dependency.
- [x] Keep dependencies reusable for later expense workflow tracks.

## Phase 8: Routes And App Registration

- [x] Add `app/api/routes/auth.py`.
- [x] Add `POST /api/v1/auth/register`.
- [x] Add `POST /api/v1/auth/login`.
- [x] Add `GET /api/v1/auth/me`.
- [x] Add `app/api/routes/users.py`.
- [x] Add `GET /api/v1/users`.
- [x] Add `POST /api/v1/users`.
- [x] Add `GET /api/v1/users/{user_id}`.
- [x] Add `PATCH /api/v1/users/{user_id}`.
- [x] Add `POST /api/v1/users/{user_id}/deactivate`.
- [x] Register `/api/v1` routers in the FastAPI app.
- [x] Keep `/health` public and unchanged.

## Phase 9: Error Handling

- [x] Add application error types if needed.
- [x] Add exception handlers or route-level conversions for consistent error shapes where practical.
- [x] Map duplicate email to `409 Conflict`.
- [x] Map invalid credentials and invalid tokens to `401 Unauthorized`.
- [x] Map role failures to `403 Forbidden`.
- [x] Map missing users to `404 Not Found`.
- [x] Confirm FastAPI validation errors remain acceptable or are adapted intentionally.

## Phase 10: Tests

- [x] Add fixtures for isolated database sessions.
- [x] Add fixtures or helpers for employee, manager, accountant, and admin users.
- [x] Test registration creates an employee and hides password hashes.
- [x] Test registration rejects duplicate email.
- [x] Test login succeeds with valid active credentials.
- [x] Test login fails with wrong password.
- [x] Test login fails for inactive users.
- [x] Test `/auth/me` succeeds with a valid token.
- [x] Test `/auth/me` fails without a token.
- [x] Test `/auth/me` fails with an invalid or expired token.
- [x] Test admin can create users with elevated roles.
- [x] Test non-admin cannot create elevated users.
- [x] Test admin can list users with pagination.
- [x] Test user list filters by role and active status.
- [x] Test admin can read, update, deactivate, and optionally reactivate users.
- [x] Test normal user can read themself if supported.
- [x] Test normal user cannot read another user if forbidden by the selected behavior.
- [x] Confirm existing health tests still pass.

## Phase 11: Verification And Context Sync

- [x] Run the full Pytest suite.
- [x] Render Alembic upgrade SQL offline; live PostgreSQL upgrade remains for a running local DB.
- [x] Confirm generated OpenAPI docs include auth and user endpoints.
- [x] Confirm no password hash appears in public API responses.
- [x] Confirm Docker Compose can still render configuration.
- [x] Update this plan with completed tasks.
- [x] Update `conductor/tracks.md` status after implementation and verification.
- [x] Record any deferred auth follow-ups as proposed tracks.

## Test Strategy

Minimum test coverage for this track:

- Service tests for password hashing, credential authentication, duplicate email behavior, inactive user behavior, and admin user management rules.
- API tests for auth endpoints, protected endpoint behavior, role boundaries, and public response shapes.
- Repository or integration tests for user lookup, uniqueness, pagination, and filters where useful.
- Migration verification through local Alembic upgrade when PostgreSQL is available.

Tests should be isolated, repeatable, and independent of execution order.

## Verification Commands

Recommended commands after implementation:

```text
.\.venv\Scripts\python -m pytest
```

```text
.\.venv\Scripts\python -m alembic upgrade head
```

```text
docker compose config
```

```text
docker compose up --build
```

Use Docker and Alembic commands only when the local environment has the required services available.

## Rollback Notes

This track will introduce the first application table and migration. Rollback should:

- Downgrade or reverse the Alembic migration if data can be discarded.
- Remove auth/user route registration.
- Remove auth/user schemas, services, repositories, dependencies, and model files.
- Preserve scaffold files from `track-001-project-scaffold`.

Because user records may be referenced by later tracks, rollback after dependent tracks are implemented will require extra care.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Password hashes or token data leak in responses or logs | Use explicit response schemas and never log sensitive values. |
| Auth logic spreads into route handlers | Keep hashing, credential validation, and token creation in services/security helpers. |
| Role checks are inconsistent across endpoints | Centralize current-user and role dependencies. |
| Tests become coupled to local PostgreSQL state | Use isolated fixtures and deterministic setup/teardown. |
| Migration adds fields later tracks need to change | Follow `database-schema.md` now while keeping expense-specific tables out of scope. |
| Registration allows privilege escalation | Public registration must always create `employee` users only. |

## Definition Of Done

- [x] Spec and plan are approved.
- [x] User model and migration are implemented.
- [x] Auth and user schemas are implemented.
- [x] Security helpers are implemented.
- [x] User repository and services are implemented.
- [x] Auth and user API routes are implemented.
- [x] Current-user and role dependencies are reusable by later tracks.
- [x] Tests cover success paths, failures, and authorization boundaries.
- [x] Verification commands pass where applicable.
- [x] Track status is updated in `conductor/tracks.md`.
