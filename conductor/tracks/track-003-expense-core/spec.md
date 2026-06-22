# Spec: Expense Request Core Workflow

## Track

`track-003-expense-core`

## Status

`verified`

## Problem Statement

The project now has a working backend scaffold plus authentication, user management, role dependencies, and a development admin bootstrap path. It does not yet allow authenticated users to create or manage expense requests.

Future manager approval, accounting review, payment tracking, and audit history tracks all depend on a stable expense domain model and core requester workflow. This track introduces the foundational expense request lifecycle while avoiding approval and payment behavior.

## Goals

- Add persistent expense request storage.
- Add receipt metadata storage for expense-created payloads.
- Add basic audit log storage for expense create, update, submit, and cancel events.
- Add expense status and category enum values.
- Add Pydantic schemas for expense create, update, response, receipt metadata, cancel, filtering, and pagination.
- Add repository and service layers for expense creation, listing, detail, updates, submission, and cancellation.
- Add API routes under `/api/v1/expenses`.
- Enforce authenticated access to all expense endpoints.
- Enforce requester/admin ownership rules for detail, update, submit, and cancel actions.
- Enforce role-based visibility for list/detail at the level needed by this track.
- Enforce valid core status transitions: draft to submitted, returned-to-employee to submitted, draft to cancelled, submitted to cancelled, returned-to-employee to cancelled.
- Keep later approval, accounting, payment, and public audit-log API behavior out of scope.
- Add tests for API behavior, service workflow rules, authorization boundaries, and response shapes.

## Non-Goals

- Do not implement manager approval, manager rejection, or return-to-employee actions.
- Do not implement accountant review, accounting rejection, payment pending, or paid actions.
- Do not implement the public audit history retrieval endpoint.
- Do not implement real file upload, OCR, receipt image storage, or receipt processing.
- Do not implement email, Slack, or push notifications.
- Do not implement policy limits, budget checks, or reimbursement calculations.
- Do not implement department tables or multi-company tenant isolation.
- Do not build a frontend.

## Users Affected

- Employees who need to create, view, update, submit, and cancel their own expense requests.
- Admins who need visibility across all expense requests and administrative correction ability within the limited core workflow.
- Managers and accountants who need later tracks to build on stable expense data.
- Developers implementing approval, payment, and audit tracks after this foundation is in place.

## Functional Requirements

### Expense Model

Create an `expenses` table aligned with `database-schema.md`.

Required fields:

- `id`
- `requester_id`
- `assigned_manager_id`
- `title`
- `description`
- `category`
- `amount`
- `currency`
- `status`
- `expense_date`
- `department`
- `project_code`
- `submitted_at`
- `manager_decided_at`
- `accountant_decided_at`
- `paid_at`
- `cancelled_at`
- `created_at`
- `updated_at`

Required behavior:

- Expense IDs should be UUIDs.
- `requester_id` is the authenticated user creating the expense.
- `status` defaults to `draft`.
- `amount` must be positive.
- `currency` must be a three-letter uppercase code.
- `title` must be non-empty.
- `category` must use supported category values.
- `department` and `project_code` are optional snapshots supplied by the request.
- `assigned_manager_id` may be set later by this track only if the input supports it and the user exists.

### Receipt Metadata

Create an `expense_receipts` table aligned with `database-schema.md`.

Required behavior:

- Expense creation may include optional receipt metadata.
- Receipt metadata stores references only, not binary files.
- At least one receipt metadata field should be present when a receipt object is supplied.
- Receipt records should reference the expense and uploading user.
- Updating receipt records after creation is not required in this track unless implementation chooses to support a simple replacement.

### Audit Log Foundation

Create an `audit_logs` table sufficient for core expense events.

Required behavior:

- Create audit log entries for expense creation, update, submit, and cancellation.
- Audit rows include expense ID, actor ID, event type, previous status, new status, comment, optional metadata, and timestamp.
- Audit retrieval endpoint remains out of scope for this track.
- Later approval/payment tracks should be able to reuse this audit log foundation.

### Create Expense

Expose:

```text
POST /api/v1/expenses
```

Required role: authenticated active user.

Required behavior:

- Creates an expense for the current user.
- Initial status is `draft`.
- Creates receipt metadata if supplied.
- Creates an `expense_created` audit entry.
- Returns the expense response shape.

### List Expenses

Expose:

```text
GET /api/v1/expenses
```

Required role: authenticated active user.

Visibility rules for this track:

- Employees see their own expenses.
- Admins see all expenses.
- Managers may see expenses assigned to them or submitted by their direct reports when the data supports those relationships.
- Accountants may see no additional scope until accounting workflow exists, or may see all submitted/approved statuses only if explicitly implemented.

Recommended default for this track:

- Implement employee self-scope and admin all-scope.
- If manager/accountant visibility is deferred, document that as a follow-up for approval/accounting tracks.

Filtering:

- `status`
- `category`
- `requester_id`
- `from_date`
- `to_date`
- `limit`
- `offset`

Required behavior:

- Non-admin users cannot use `requester_id` to escape their allowed visibility.
- Responses use the standard paginated response shape.

### Get Expense

Expose:

```text
GET /api/v1/expenses/{expense_id}
```

Required role: authenticated active user with access to the expense.

Required behavior:

- Requester can read their own expense.
- Admin can read any expense.
- Unauthorized users should receive `403 Forbidden` or hidden-resource `404 Not Found`, following the selected behavior.

### Update Expense

Expose:

```text
PATCH /api/v1/expenses/{expense_id}
```

Required role: requester or admin.

Allowed statuses:

- `draft`
- `returned_to_employee`

Required behavior:

- Allow updates to editable core fields only.
- Do not allow direct status changes through this endpoint.
- Do not allow edits after submission unless status is `returned_to_employee`.
- Create an `expense_updated` audit entry when a meaningful change is applied.

Editable fields:

- `title`
- `description`
- `category`
- `amount`
- `currency`
- `expense_date`
- `department`
- `project_code`
- optional receipt metadata behavior if chosen during implementation

### Submit Expense

Expose:

```text
POST /api/v1/expenses/{expense_id}/submit
```

Required role: requester or admin.

Allowed statuses:

- `draft`
- `returned_to_employee`

Resulting status:

- `submitted`

Required behavior:

- Set `submitted_at`.
- Create an `expense_submitted` audit entry.
- Reject invalid status transitions with `400 Bad Request` or `409 Conflict`.

### Cancel Expense

Expose:

```text
POST /api/v1/expenses/{expense_id}/cancel
```

Required role: requester or admin.

Allowed statuses:

- `draft`
- `submitted`
- `returned_to_employee`

Resulting status:

- `cancelled`

Required behavior:

- Accept an optional or required reason. Recommended default: require a reason.
- Set `cancelled_at`.
- Create an `expense_cancelled` audit entry.
- Reject invalid status transitions.

## API Behavior

Base path:

```text
/api/v1
```

### Create Expense

```text
POST /api/v1/expenses
```

Request:

```json
{
  "title": "Client lunch",
  "description": "Lunch with client after project meeting.",
  "category": "meals",
  "amount": "45.75",
  "currency": "USD",
  "expense_date": "2026-06-18",
  "department": "Sales",
  "project_code": "ACME-001",
  "receipt": {
    "url": "https://example.com/receipts/receipt-123.pdf",
    "file_name": "receipt-123.pdf",
    "content_type": "application/pdf"
  }
}
```

Response:

```json
{
  "id": "expense-id",
  "requester_id": "user-id",
  "title": "Client lunch",
  "description": "Lunch with client after project meeting.",
  "category": "meals",
  "amount": "45.75",
  "currency": "USD",
  "status": "draft",
  "expense_date": "2026-06-18",
  "department": "Sales",
  "project_code": "ACME-001",
  "created_at": "2026-06-19T05:00:00Z",
  "updated_at": "2026-06-19T05:00:00Z"
}
```

### List Expenses

```text
GET /api/v1/expenses
```

Response:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

### Get Expense

```text
GET /api/v1/expenses/{expense_id}
```

### Update Expense

```text
PATCH /api/v1/expenses/{expense_id}
```

### Submit Expense

```text
POST /api/v1/expenses/{expense_id}/submit
```

### Cancel Expense

```text
POST /api/v1/expenses/{expense_id}/cancel
```

Request:

```json
{
  "reason": "Submitted by mistake."
}
```

## Data Model Implications

Add these tables:

- `expenses`
- `expense_receipts`
- `audit_logs`

Migration should include:

- UUID primary keys.
- Foreign keys to `users`.
- Constraints for amount, currency, status, category, and non-empty title.
- Recommended indexes from `database-schema.md`.
- JSON/JSONB metadata support for receipts and audit logs where practical.

No approval decision or payment tables should be added in this track unless required by shared model dependencies.

## Authorization Rules

- All expense endpoints require an active authenticated user.
- Requesters can create expenses for themselves.
- Requesters can read, update, submit, and cancel their own eligible expenses.
- Admins can read, update, submit, and cancel any eligible expense.
- Non-admin users cannot access another requester's expense in this track.
- Non-admin users cannot bypass visibility by passing another `requester_id` filter.
- Role checks and ownership checks must occur before exposing protected records where practical.

## Acceptance Criteria

- SQLAlchemy models and Alembic migration exist for expenses, receipt metadata, and audit logs.
- Expense create endpoint creates a draft expense for the current user.
- Optional receipt metadata is persisted when supplied.
- Expense list endpoint returns paginated results scoped to the current user's visibility.
- Expense detail endpoint enforces ownership/admin access.
- Expense update endpoint works only for `draft` and `returned_to_employee`.
- Expense submit endpoint transitions eligible expenses to `submitted` and sets `submitted_at`.
- Expense cancel endpoint transitions eligible expenses to `cancelled` and sets `cancelled_at`.
- Invalid status transitions are rejected consistently.
- Core expense events create audit log rows.
- Tests cover success paths, validation failures, authorization failures, filters, pagination, and invalid transitions.
- Existing auth/user tests continue to pass.

## Open Decisions

- Resolved: manager/accountant read visibility is deferred beyond admin/self-scope.
- Resolved: cancel reason is required.
- Resolved: receipt metadata is creation-only for this track.
- Resolved: unauthorized access to another user's expense returns `403`.
- Resolved: audit log retrieval remains deferred to `track-006-audit-history`.
