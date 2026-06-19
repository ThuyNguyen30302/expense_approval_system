# Database Schema Design

## Overview

The Expense Approval System uses **PostgreSQL only** as the application database.

PostgreSQL is the source of truth for:

- users
- expense requests
- receipt metadata
- approval decisions
- payment records
- audit history
- flexible event metadata through JSONB

No migrations are defined in this document. This is a schema design reference for future SQLAlchemy models and Alembic migrations.

## Design Principles

- Keep all authoritative data in PostgreSQL.
- Use relational tables for core workflow data.
- Use JSONB only for flexible metadata that does not need frequent joins or strict constraints.
- Store money as fixed-precision decimals, not floating point.
- Record every meaningful status transition in `audit_logs`.
- Keep the current expense status on the `expenses` row for efficient filtering.
- Keep historical decisions in append-only tables.
- Do not physically delete users or expenses in normal workflows.

## SQL Tables

## `users`

Stores authenticated users and their role.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `email` | VARCHAR(255) | No | Unique, normalized lowercase. |
| `full_name` | VARCHAR(255) | No | User display name. |
| `hashed_password` | VARCHAR(255) | No | Password hash only. Never store plaintext passwords. |
| `role` | ENUM / VARCHAR(32) | No | One of `employee`, `manager`, `accountant`, `admin`. |
| `manager_id` | UUID | Yes | Self-reference to `users.id`; useful for employee-manager visibility. |
| `department` | VARCHAR(120) | Yes | Optional department used for filtering and manager workflows. |
| `is_active` | BOOLEAN | No | Defaults to `true`. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |
| `updated_at` | TIMESTAMPTZ | No | UTC timestamp. |
| `deactivated_at` | TIMESTAMPTZ | Yes | Set when user is deactivated. |

### Relationships

- One manager can have many employee users through `users.manager_id`.
- One user can submit many expenses.
- One user can upload many receipts.
- One user can act on many approvals, payments, and audit records.

### Constraints

- Primary key on `id`.
- Unique index on `email`.
- Check `email` is not empty.
- Check `role` is one of the supported roles.
- Check `manager_id != id`.
- `manager_id` references `users.id` with `ON DELETE SET NULL`.
- If `is_active = false`, `deactivated_at` should be set by application logic.

### Recommended Indexes

- `idx_users_role`
- `idx_users_manager_id`
- `idx_users_department`
- `idx_users_is_active`

## `expenses`

Stores the current state and core fields of each expense request.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `requester_id` | UUID | No | References `users.id`. |
| `assigned_manager_id` | UUID | Yes | References `users.id`; manager responsible for approval. |
| `title` | VARCHAR(200) | No | Short expense title. |
| `description` | TEXT | Yes | Expense details. |
| `category` | ENUM / VARCHAR(40) | No | Suggested values listed below. |
| `amount` | NUMERIC(12, 2) | No | Must be greater than zero. |
| `currency` | CHAR(3) | No | Uppercase ISO-style currency code. |
| `status` | ENUM / VARCHAR(40) | No | Current workflow status. |
| `expense_date` | DATE | No | Date expense occurred. |
| `department` | VARCHAR(120) | Yes | Optional department snapshot. |
| `project_code` | VARCHAR(80) | Yes | Optional project or cost center code. |
| `submitted_at` | TIMESTAMPTZ | Yes | Set when expense is submitted. |
| `manager_decided_at` | TIMESTAMPTZ | Yes | Set after manager approval or rejection. |
| `accountant_decided_at` | TIMESTAMPTZ | Yes | Set after accountant approval or rejection. |
| `paid_at` | TIMESTAMPTZ | Yes | Set when payment is completed. |
| `cancelled_at` | TIMESTAMPTZ | Yes | Set when expense is cancelled. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |
| `updated_at` | TIMESTAMPTZ | No | UTC timestamp. |

### Relationships

- Many expenses belong to one requester.
- Many expenses may be assigned to one manager.
- One expense has zero or many receipt records.
- One expense has many approval decisions.
- One expense has zero or many payment records.
- One expense has many audit log entries.

### Constraints

- Primary key on `id`.
- `requester_id` references `users.id` with restricted deletion.
- `assigned_manager_id` references `users.id` with `ON DELETE SET NULL`.
- Check `amount > 0`.
- Check `currency` matches three uppercase letters.
- Check `status` is one of the supported expense statuses.
- Check `category` is one of the supported categories.
- Check `title` is not empty.
- Check `paid_at IS NOT NULL` when `status = 'paid'`.

Complex workflow rules should be enforced in the service layer and covered by tests.

### Recommended Indexes

- `idx_expenses_requester_id`
- `idx_expenses_assigned_manager_id`
- `idx_expenses_status`
- `idx_expenses_category`
- `idx_expenses_expense_date`
- `idx_expenses_created_at`
- Composite index on `(requester_id, status)`.
- Composite index on `(assigned_manager_id, status)`.
- Composite index on `(status, expense_date)`.

## `expense_receipts`

Stores receipt metadata for expenses. Actual file storage is out of scope; this table stores references and metadata only.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `expense_id` | UUID | No | References `expenses.id`. |
| `uploaded_by_id` | UUID | No | References `users.id`. |
| `url` | TEXT | Yes | Link to receipt file if stored externally. |
| `file_name` | VARCHAR(255) | Yes | Original or stored file name. |
| `content_type` | VARCHAR(120) | Yes | Example: `application/pdf`, `image/png`. |
| `size_bytes` | INTEGER | Yes | Must be positive when present. |
| `checksum` | VARCHAR(128) | Yes | Optional checksum for duplicate/integrity checks. |
| `metadata` | JSONB | Yes | Flexible receipt metadata. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |

### Relationships

- Many receipt records belong to one expense.
- Many receipt records are uploaded by one user.

### Constraints

- Primary key on `id`.
- `expense_id` references `expenses.id` with restricted deletion.
- `uploaded_by_id` references `users.id` with restricted deletion.
- Check `size_bytes > 0` when present.
- At least one of `url`, `file_name`, or `metadata` should be present.

### Recommended Indexes

- `idx_expense_receipts_expense_id`
- `idx_expense_receipts_uploaded_by_id`
- `idx_expense_receipts_created_at`
- Optional GIN index on `metadata` if metadata filtering becomes common.

## `approval_decisions`

Stores manager and accountant decisions. This table is an append-only decision history, not just the latest approval state.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `expense_id` | UUID | No | References `expenses.id`. |
| `actor_id` | UUID | No | User who made the decision. |
| `stage` | ENUM / VARCHAR(32) | No | `manager` or `accounting`. |
| `decision` | ENUM / VARCHAR(32) | No | `approved`, `rejected`, or `returned`. |
| `from_status` | VARCHAR(40) | No | Previous expense status. |
| `to_status` | VARCHAR(40) | No | Resulting expense status. |
| `reason` | TEXT | Yes | Required for rejections and returns. |
| `comment` | TEXT | Yes | Optional note for approvals. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |

### Constraints

- Primary key on `id`.
- `expense_id` references `expenses.id` with restricted deletion.
- `actor_id` references `users.id` with restricted deletion.
- Check `stage` is `manager` or `accounting`.
- Check `decision` is `approved`, `rejected`, or `returned`.
- Check `reason IS NOT NULL` when `decision IN ('rejected', 'returned')`.
- Check status pairs are valid for the selected stage and decision where practical.

### Recommended Indexes

- `idx_approval_decisions_expense_id`
- `idx_approval_decisions_actor_id`
- `idx_approval_decisions_stage`
- Composite index on `(expense_id, created_at)`.

## `payments`

Stores payment tracking records for approved expenses.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `expense_id` | UUID | No | References `expenses.id`. |
| `actor_id` | UUID | No | Accountant or admin who recorded the payment action. |
| `status` | ENUM / VARCHAR(32) | No | `payment_pending` or `paid`. |
| `payment_method` | ENUM / VARCHAR(40) | Yes | Suggested values listed below. |
| `payment_reference` | VARCHAR(120) | Yes | Bank reference, check number, or external reference. |
| `scheduled_at` | TIMESTAMPTZ | Yes | Optional scheduled payment time. |
| `paid_at` | TIMESTAMPTZ | Yes | Required when status is `paid`. |
| `notes` | TEXT | Yes | Optional payment note. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |
| `updated_at` | TIMESTAMPTZ | No | UTC timestamp. |

### Constraints

- Primary key on `id`.
- `expense_id` references `expenses.id` with restricted deletion.
- `actor_id` references `users.id` with restricted deletion.
- Check `status` is `payment_pending` or `paid`.
- Check `payment_method` is one of the supported methods when present.
- Check `paid_at IS NOT NULL` when `status = 'paid'`.
- Unique partial index on `payment_reference` where `payment_reference IS NOT NULL`, if references are expected to be globally unique.

### Recommended Indexes

- `idx_payments_expense_id`
- `idx_payments_actor_id`
- `idx_payments_status`
- `idx_payments_paid_at`

## `audit_logs`

Stores an append-only audit trail for expense workflow changes.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `expense_id` | UUID | No | References `expenses.id`. |
| `actor_id` | UUID | Yes | References `users.id`; nullable for system actions. |
| `event_type` | ENUM / VARCHAR(60) | No | Examples listed below. |
| `previous_status` | VARCHAR(40) | Yes | Null when expense is first created. |
| `new_status` | VARCHAR(40) | Yes | Null if event does not change status. |
| `comment` | TEXT | Yes | Human-readable reason or note. |
| `metadata` | JSONB | Yes | Flexible event context such as request info or admin correction details. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |

### Constraints

- Primary key on `id`.
- `expense_id` references `expenses.id` with restricted deletion.
- `actor_id` references `users.id` with `ON DELETE SET NULL`.
- Check `event_type` is one of supported audit event types.
- Check `previous_status` and `new_status` are valid expense statuses when present.
- Audit rows should be append-only by application policy.

### Recommended Indexes

- `idx_audit_logs_expense_id`
- `idx_audit_logs_actor_id`
- `idx_audit_logs_event_type`
- `idx_audit_logs_created_at`
- Composite index on `(expense_id, created_at)`.
- Optional GIN index on `metadata` if event metadata filtering becomes common.

## Optional Future Tables

## `refresh_tokens`

Needed only if the project adds refresh token rotation.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `user_id` | UUID | No | References `users.id`. |
| `token_hash` | VARCHAR(255) | No | Hash of refresh token. |
| `expires_at` | TIMESTAMPTZ | No | Expiration time. |
| `revoked_at` | TIMESTAMPTZ | Yes | Set when revoked. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |

## `departments`

Useful if departments need stronger structure than a text field.

| Column | Type | Nullable | Notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key. |
| `name` | VARCHAR(120) | No | Unique department name. |
| `manager_id` | UUID | Yes | References `users.id`. |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp. |
| `updated_at` | TIMESTAMPTZ | No | UTC timestamp. |

## Enums And Status Values

## User Roles

```text
employee
manager
accountant
admin
```

## Expense Statuses

```text
draft
submitted
manager_approved
manager_rejected
returned_to_employee
accountant_approved
accountant_rejected
payment_pending
paid
cancelled
```

## Expense Categories

```text
travel
meals
lodging
office_supplies
software
training
transportation
other
```

## Approval Stages

```text
manager
accounting
```

## Approval Decisions

```text
approved
rejected
returned
```

## Payment Statuses

```text
payment_pending
paid
```

## Payment Methods

```text
bank_transfer
cash
company_card
check
other
```

## Audit Event Types

```text
expense_created
expense_updated
expense_submitted
expense_cancelled
receipt_added
manager_approved
manager_rejected
expense_returned
accountant_approved
accountant_rejected
payment_pending
expense_paid
admin_corrected
```

## Status Transition Rules

The service layer should enforce status transitions. Database constraints may enforce simple invariants, but workflow validation should stay centralized in services.

| From Status | Action | To Status | Actor |
| --- | --- | --- | --- |
| `draft` | submit | `submitted` | requester or admin |
| `returned_to_employee` | submit | `submitted` | requester or admin |
| `submitted` | manager approve | `manager_approved` | manager or admin |
| `submitted` | manager reject | `manager_rejected` | manager or admin |
| `submitted` | return | `returned_to_employee` | manager or admin |
| `manager_approved` | accountant approve | `accountant_approved` | accountant or admin |
| `manager_approved` | accountant reject | `accountant_rejected` | accountant or admin |
| `manager_approved` | return | `returned_to_employee` | accountant or admin |
| `accountant_approved` | mark payment pending | `payment_pending` | accountant or admin |
| `accountant_approved` | mark paid | `paid` | accountant or admin |
| `payment_pending` | mark paid | `paid` | accountant or admin |
| `draft` | cancel | `cancelled` | requester or admin |
| `submitted` | cancel | `cancelled` | requester or admin |
| `returned_to_employee` | cancel | `cancelled` | requester or admin |

## Terminal Statuses

These statuses should generally prevent normal edits:

```text
manager_rejected
accountant_rejected
paid
cancelled
```

Admin-only correction paths may be added later, but they should create audit log entries.

## Relationship Summary

```text
users.id -> users.manager_id
users.id -> expenses.requester_id
users.id -> expenses.assigned_manager_id
users.id -> expense_receipts.uploaded_by_id
users.id -> approval_decisions.actor_id
users.id -> payments.actor_id
users.id -> audit_logs.actor_id

expenses.id -> expense_receipts.expense_id
expenses.id -> approval_decisions.expense_id
expenses.id -> payments.expense_id
expenses.id -> audit_logs.expense_id
```

## DBeaver Management Notes

With PostgreSQL running through Docker Compose, connect DBeaver Community using:

```text
Host: localhost
Port: 5432
Database: expense_approval
Username: expense_user
Password: expense_password
```

After migrations are created in later tracks, DBeaver can be used to:

- inspect tables, columns, constraints, and indexes
- view and edit table rows
- run SQL queries
- inspect JSONB metadata values
- export/import development data

## Important Implementation Notes

- Prefer UUID primary keys for public API friendliness and reduced ID guessing.
- Use timezone-aware UTC timestamps, represented as `TIMESTAMPTZ`.
- Use `NUMERIC(12, 2)` for expense amounts unless higher precision is needed.
- Normalize email to lowercase before storing.
- Keep `expenses.status` as the current status for fast list filtering.
- Keep historical decisions in `approval_decisions`.
- Keep historical transitions in `audit_logs`.
- Store receipt metadata in `expense_receipts`.
- Use JSONB only for flexible metadata, not core workflow state.
- Enforce complex workflow rules in the service layer and cover them with tests.
