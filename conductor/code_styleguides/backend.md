# Backend Code Style Guide

## Layering

- Keep API routes thin.
- Keep workflow rules in services.
- Keep database access in repositories or focused data-access helpers.
- Keep Pydantic schemas separate from SQLAlchemy models.

## Naming

- Use explicit domain names: `expense`, `approval`, `payment`, `audit_log`.
- Use role names consistently: `employee`, `manager`, `accountant`, `admin`.
- Use enum values consistently with documented API statuses.

## Services

Service functions should:

- Validate permissions.
- Validate current workflow status.
- Apply state changes.
- Create audit log records.
- Return domain objects or response-ready data.

## Tests

Every workflow transition should have tests for:

- valid transition
- invalid source status
- unauthorized role
- missing required reason where applicable
- audit log creation

## Error Handling

- Use consistent application exceptions.
- Map exceptions to predictable HTTP responses.
- Do not leak internal stack traces or database details.

