# Plan: Expense Request Core Workflow

## Track

`track-003-expense-core`

## Status

`done`

## Implementation Phases

## Phase 1: Context And Scope Confirmation

- [x] Re-read the relevant sections of `product-requirements.md`, `api-design.md`, `backend-architecture.md`, `coding-rules.md`, and `database-schema.md`.
- [x] Confirm `track-002-auth-users` is complete and reusable.
- [x] Confirm this track excludes manager approval, accounting review, payment tracking, and audit history API retrieval.
- [x] Decide final behavior for manager/accountant visibility in this track.
- [x] Decide final behavior for cancel reason requirement.
- [x] Decide final behavior for receipt metadata updates.

## Phase 2: Domain Types And Persistence Models

- [x] Add expense status enum values.
- [x] Add expense category enum values.
- [x] Add audit event type enum values needed by core expense workflow.
- [x] Create the SQLAlchemy `Expense` model.
- [x] Create the SQLAlchemy `ExpenseReceipt` model.
- [x] Create the SQLAlchemy `AuditLog` model.
- [x] Add relationships between users, expenses, receipts, and audit logs where useful.
- [x] Register models with SQLAlchemy metadata.
- [x] Add an Alembic migration for `expenses`, `expense_receipts`, and `audit_logs`.
- [x] Include indexes and constraints from `database-schema.md`.
- [x] Verify the migration is reversible where practical.

## Phase 3: Schemas And Validation

- [x] Add receipt metadata request and response schemas.
- [x] Add expense create schema.
- [x] Add expense update schema.
- [x] Add expense response schema.
- [x] Add expense list paginated response schema.
- [x] Add expense cancel request schema.
- [x] Add filter/query schemas or dependency helpers for status, category, requester, date range, limit, and offset.
- [x] Validate positive amount.
- [x] Validate uppercase three-letter currency.
- [x] Validate non-empty title.
- [x] Validate supported status and category values with enums.
- [x] Keep response models stable and avoid exposing internal-only fields.

## Phase 4: Repositories

- [x] Add expense repository helpers for create, get by ID, list with filters, update, and count.
- [x] Add receipt repository helpers for create and read by expense ID where needed.
- [x] Add audit log repository helper for appending core events.
- [x] Keep commits outside low-level repository helpers unless the helper explicitly owns a transaction.
- [x] Ensure query helpers can apply visibility scopes and filters predictably.

## Phase 5: Services And Business Rules

- [x] Add expense service for create, list, get, update, submit, and cancel.
- [x] Set requester from the current authenticated user, not request body.
- [x] Default new expenses to `draft`.
- [x] Create receipt metadata during expense creation when supplied.
- [x] Create audit entries for create, update, submit, and cancel.
- [x] Enforce requester/admin access.
- [x] Enforce list visibility and prevent requester filter escalation.
- [x] Enforce update eligibility for `draft` and `returned_to_employee` only.
- [x] Enforce submit eligibility for `draft` and `returned_to_employee` only.
- [x] Enforce cancel eligibility for `draft`, `submitted`, and `returned_to_employee` only.
- [x] Set `submitted_at` and `cancelled_at` during transitions.
- [x] Keep route handlers thin.

## Phase 6: API Routes And Registration

- [x] Add `app/api/routes/expenses.py`.
- [x] Add `POST /api/v1/expenses`.
- [x] Add `GET /api/v1/expenses`.
- [x] Add `GET /api/v1/expenses/{expense_id}`.
- [x] Add `PATCH /api/v1/expenses/{expense_id}`.
- [x] Add `POST /api/v1/expenses/{expense_id}/submit`.
- [x] Add `POST /api/v1/expenses/{expense_id}/cancel`.
- [x] Register the expenses router under `/api/v1`.
- [x] Keep existing auth/user routes unchanged.

## Phase 7: Error Handling

- [x] Reuse existing application error shape.
- [x] Map invalid status transitions to `400 Bad Request` or `409 Conflict`.
- [x] Map unauthorized access to `403 Forbidden` or selected hidden-resource behavior.
- [x] Map missing expenses to `404 Not Found`.
- [x] Map validation failures through Pydantic `422 Unprocessable Entity`.
- [x] Ensure internal database errors are not exposed raw to clients.

## Phase 8: Tests

- [x] Add fixtures or helpers for users and auth tokens if current fixtures are insufficient.
- [x] Test employee can create draft expense.
- [x] Test receipt metadata is persisted when supplied.
- [x] Test create validates amount, currency, title, and category.
- [x] Test employee list returns only their own expenses.
- [x] Test admin list returns all expenses.
- [x] Test filters by status, category, requester, and date range.
- [x] Test pagination limit and offset.
- [x] Test requester can read own expense.
- [x] Test non-admin cannot read another user's expense.
- [x] Test admin can read any expense.
- [x] Test requester can update own draft expense.
- [x] Test update rejects submitted expenses.
- [x] Test update rejects another user's expense.
- [x] Test submit transitions draft to submitted and sets `submitted_at`.
- [x] Test submit rejects invalid statuses.
- [x] Test cancel transitions eligible expense to cancelled and sets `cancelled_at`.
- [x] Test cancel rejects invalid statuses.
- [x] Test audit rows are created for create, update, submit, and cancel.
- [x] Confirm existing auth/user and health tests still pass.

## Phase 9: Verification And Context Sync

- [x] Run the full Pytest suite.
- [x] Render Alembic upgrade SQL offline.
- [ ] Run Alembic upgrade against a local PostgreSQL database if available.
- [x] Confirm generated OpenAPI docs include expense endpoints.
- [x] Confirm Docker Compose can still render configuration.
- [x] Update this plan with completed tasks.
- [x] Update `conductor/tracks.md` status after implementation and verification.
- [x] Record deferred approval, accounting, payment, and audit retrieval work in proposed tracks if needed.

## Test Strategy

Minimum test coverage for this track:

- Service tests for core status transitions and ownership rules.
- API tests for create, list, detail, update, submit, cancel, filters, pagination, and permission failures.
- Persistence tests or integration tests for receipt metadata and audit log creation.
- Migration verification through local Alembic upgrade when PostgreSQL is available.

Tests should remain isolated, repeatable, and independent of execution order.

## Verification Commands

Recommended commands after implementation:

```text
.\.venv\Scripts\python -m pytest
```

If the local venv launcher is unavailable, use the known working fallback from the current environment:

```text
$env:PYTHONPATH = ".\.venv\Lib\site-packages"; C:\Users\CarrotDay\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
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

Use Docker and live Alembic commands only when the local environment has the required services available.

## Rollback Notes

This track will introduce expense, receipt, and audit log tables. Rollback should:

- Downgrade or reverse the Alembic migration if data can be discarded.
- Remove expense route registration.
- Remove expense schemas, services, repositories, and model files.
- Preserve auth/user behavior from `track-002-auth-users`.

Once later approval/payment tracks depend on these tables, rollback will require extra care.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Scope expands into approval or payment behavior | Keep this track limited to create/list/detail/update/submit/cancel. |
| Authorization leaks another user's expense | Centralize visibility and ownership checks in the service layer and test boundaries. |
| Workflow rules spread into route handlers | Keep status transitions in the expense service. |
| Money precision issues | Use decimal-compatible schemas and `NUMERIC(12, 2)` persistence. |
| Audit logging becomes inconsistent | Add one helper for appending audit entries and test each core event. |
| Receipt metadata turns into file upload scope | Store references only; defer binary storage and upload handling. |

## Definition Of Done

- [x] Spec and plan are approved.
- [x] Expense, receipt, and audit models are implemented.
- [x] Alembic migration is implemented.
- [x] Expense schemas are implemented.
- [x] Expense repository and service are implemented.
- [x] Expense API routes are implemented.
- [x] Ownership and role visibility rules are enforced.
- [x] Core transitions create audit rows.
- [x] Tests cover success paths, failures, authorization boundaries, filters, pagination, and status transitions.
- [x] Verification commands pass where applicable.
- [x] Track status is updated in `conductor/tracks.md`.
- [x] Track is marked done after review follow-ups.
