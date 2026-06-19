# Coding Rules

## General Principles

- Keep the codebase simple, explicit, and easy to review.
- Prefer small modules with clear responsibilities.
- Keep business logic in services, not route handlers.
- Do not introduce abstractions before they remove real duplication or clarify workflow rules.
- Treat documentation, tests, and migrations as part of the implementation.

## Python Style

- Use modern Python type hints.
- Prefer readable names over abbreviations.
- Keep functions focused on one responsibility.
- Use explicit returns.
- Avoid broad exception catches unless converting to a known application error.
- Do not leave dead code, commented-out code, or debug prints.

## FastAPI Rules

- Keep route handlers thin.
- Use dependency injection for:
  - current user
  - database session
  - role checks
  - pagination parameters
- Use `APIRouter` per feature area.
- Use clear tags for OpenAPI grouping.
- Return Pydantic response schemas from API routes.
- Do not return raw ORM objects unless response serialization is intentionally configured.

## Pydantic Rules

- Create separate schemas for create, update, and response shapes.
- Never expose password hashes.
- Validate domain constraints close to the API boundary when practical.
- Use enums for stable values such as role, expense status, payment status, and category.
- Keep response models stable and client-friendly.

## SQLAlchemy Rules

- Keep SQLAlchemy models focused on persistence.
- Use relationships where they clarify querying and domain navigation.
- Prefer explicit indexes for frequently filtered columns such as user ID, status, and created timestamp.
- Use transactions around workflow state changes.
- Avoid committing inside low-level repository helpers unless the repository method explicitly owns the transaction.

## Alembic Rules

- Every SQL schema change must have a migration.
- Migration filenames should describe the change.
- Migrations should be reversible when reasonable.
- Do not edit already-applied migrations unless the project is still pre-release and the migration history is intentionally being reset.

## PostgreSQL Metadata Rules

- Use PostgreSQL as the only application database.
- Use JSON/JSONB columns only for flexible metadata that does not need heavy relational querying.
- Keep JSON/JSONB shapes documented in schemas or model comments where possible.
- Do not store authoritative workflow state inside JSON/JSONB fields.
- Prefer normal relational columns for fields that are filtered, joined, indexed, or constrained frequently.

## Authentication And Security

- Passwords must always be hashed with a secure password hashing library.
- JWT secrets must come from environment variables.
- Never log passwords, tokens, or sensitive payment details.
- Always check both role and ownership where needed.
- Use secure defaults for token expiration.
- Return generic authentication errors.

## Business Logic Rules

- Expense workflow transitions must be centralized in the service layer.
- Rejections must include a reason.
- Paid expenses are immutable except for admin-only correction paths.
- Every status transition must create an audit log entry.
- Authorization should be checked before revealing whether a protected record exists.
- Workflow state should be represented by enums, not free-form strings.

## API Design Rules

- Use plural nouns for resource paths.
- Use standard HTTP methods:
  - `GET` for retrieval
  - `POST` for creation and workflow actions
  - `PATCH` for partial updates
  - `DELETE` only for true deletion or cancellation if explicitly designed that way
- Use consistent pagination parameters: `limit` and `offset`.
- Use ISO 8601 timestamps in API responses.
- Use consistent error response bodies.

## Testing Rules

- New business rules require tests.
- New endpoints require API tests for success and permission failures.
- Workflow changes require tests for valid and invalid transitions.
- Tests should not depend on execution order.
- Use factories or fixtures for test data.
- Keep tests readable and focused on behavior.

## Docker And Environment Rules

- Local development should run through Docker Compose.
- Environment variables should be documented in an example env file.
- Do not commit real secrets.
- Containers should fail fast if required configuration is missing.

## Git And Review Rules

- Keep commits focused.
- Include migrations with model changes.
- Include tests with behavior changes.
- Prefer clear PR descriptions that mention:
  - what changed
  - why it changed
  - how it was tested
