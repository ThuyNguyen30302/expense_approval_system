# Product Requirements

## Product Overview

Expense Approval System is a backend service for managing company expense requests from submission through approval, accounting review, and payment tracking.

The project is intended as a personal portfolio backend demonstrating production-minded API design, authentication, authorization, persistence, testing, migrations, and containerized development.

## Goals

- Allow employees to submit expense requests with category, amount, currency, description, and receipt metadata.
- Allow managers to approve or reject submitted expenses.
- Allow accountants to review approved expenses before payment.
- Track payment status after accounting review.
- Provide role-based access control for employees, managers, accountants, and administrators.
- Maintain an auditable status history for each expense request.
- Expose a clean FastAPI REST API with validation, authentication, and predictable error responses.
- Support local development and testing with Docker.

## Non-Goals

- No frontend application in the initial scope.
- No real payment processor integration in the initial scope.
- No OCR or receipt image processing in the initial scope.
- No email, Slack, or push notification delivery in the initial scope.
- No multi-company tenant isolation unless added later.

## User Roles

### Employee

- Can register or be created by an admin.
- Can authenticate and manage their own profile.
- Can submit expense requests.
- Can view their own expense requests.
- Can update draft or returned expense requests.
- Can cancel eligible expense requests.

### Manager

- Can view expense requests assigned to them or submitted by employees in their team.
- Can approve expense requests.
- Can reject expense requests with a reason.
- Can return expense requests for changes.

### Accountant

- Can view manager-approved expense requests.
- Can mark expenses as reviewed.
- Can reject expenses during accounting review with a reason.
- Can mark reviewed expenses as paid.
- Can record payment details such as payment date, reference number, and notes.

### Admin

- Can manage users and roles.
- Can view all expense requests.
- Can correct administrative data when required.

## Core Workflow

1. Employee creates an expense request as a draft or submits it for review.
2. Submitted expense enters manager review.
3. Manager approves, rejects, or returns the request.
4. Approved expense enters accountant review.
5. Accountant reviews and either rejects, returns, or marks it ready for payment.
6. Accountant records payment.
7. Expense reaches paid status.

## Expense Statuses

- `draft`: Created but not submitted.
- `submitted`: Awaiting manager decision.
- `manager_approved`: Approved by manager and awaiting accountant review.
- `manager_rejected`: Rejected by manager.
- `returned_to_employee`: Returned for employee edits.
- `accountant_approved`: Reviewed by accountant and ready for payment.
- `accountant_rejected`: Rejected by accountant.
- `payment_pending`: Payment is scheduled or in progress.
- `paid`: Payment has been completed.
- `cancelled`: Cancelled by employee or admin before completion.

## Functional Requirements

### Authentication

- Users can log in with email and password.
- API issues JWT access tokens.
- Passwords are hashed before storage.
- Protected endpoints require valid authentication.
- Authorization is role-based.

### User Management

- Store users with email, full name, hashed password, role, active status, and timestamps.
- Enforce unique email addresses.
- Admins can create, update, deactivate, and list users.
- Users can view their own profile.

### Expense Requests

- Employees can create expense requests with:
  - title
  - description
  - category
  - amount
  - currency
  - expense date
  - receipt URL or receipt metadata
  - optional project or department
- Expense amount must be positive.
- Currency should use ISO-style uppercase codes such as `USD`, `VND`, or `EUR`.
- Submitted expenses cannot be edited unless returned to the employee.
- Every status change should create an audit/history entry.

### Approval

- Managers can approve or reject submitted expenses.
- Rejections require a reason.
- Approval captures approver identity and timestamp.
- Manager approval moves the expense to accountant review.

### Accounting Review

- Accountants can review manager-approved expenses.
- Accountants can approve for payment, reject, or return for correction.
- Accounting decisions should include reviewer identity and timestamp.
- Rejections require a reason.

### Payment Tracking

- Accountants can mark accountant-approved expenses as payment pending.
- Accountants can mark payment pending expenses as paid.
- Payment records include:
  - payment status
  - paid date
  - payment method
  - payment reference
  - notes

### Audit Trail

- Each meaningful state transition should be logged.
- History entries should include:
  - expense ID
  - previous status
  - new status
  - actor ID
  - comment or reason
  - timestamp

## Data Requirements

- Use PostgreSQL via SQLAlchemy for users, expenses, approvals, payments, audit history, receipt metadata, and structured event details.
- Use PostgreSQL JSON/JSONB columns for flexible metadata when a full relational shape is unnecessary.
- Database migrations are managed with Alembic.

## API Requirements

- RESTful JSON API.
- FastAPI-generated OpenAPI documentation should be available in development.
- Consistent response and error shapes.
- Pagination for list endpoints.
- Filtering for expense status, category, date range, requester, and reviewer where appropriate.

## Security Requirements

- Never store plaintext passwords.
- Validate JWT signature and expiration.
- Enforce role checks on protected routes.
- Prevent users from accessing expenses they are not allowed to see.
- Validate all request bodies with Pydantic schemas.
- Avoid exposing internal errors in API responses.

## Testing Requirements

- Unit tests for service-layer business rules.
- API tests for authentication, authorization, and major workflows.
- Database tests for repository behavior where useful.
- Tests should run with Pytest.
- Test data should be isolated and repeatable.

## Success Criteria

- A developer can understand the product scope from documentation alone.
- The backend can later be implemented incrementally from clear requirements.
- Main workflows are explicit enough to guide test scenarios.
- Role boundaries and status transitions are clear.
