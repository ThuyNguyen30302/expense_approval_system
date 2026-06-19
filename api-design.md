# API Design

## API Overview

The Expense Approval System API is a RESTful JSON API built with FastAPI.

Base path:

```text
/api/v1
```

Authentication uses JWT bearer tokens:

```text
Authorization: Bearer <access_token>
```

## Common Conventions

### Timestamps

Use ISO 8601 timestamps in UTC.

Example:

```json
"2026-06-19T05:00:00Z"
```

### Pagination

List endpoints should support:

```text
limit=20
offset=0
```

Default `limit` should be reasonable, such as `20`. Maximum `limit` should be capped, such as `100`.

Paginated responses should use a consistent shape:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

### Error Shape

Application errors should use a consistent shape:

```json
{
  "error": {
    "code": "expense_invalid_status_transition",
    "message": "Expense cannot be approved from its current status.",
    "details": {}
  }
}
```

### Roles

Supported roles:

- `employee`
- `manager`
- `accountant`
- `admin`

## Authentication Endpoints

### Register User

```text
POST /api/v1/auth/register
```

Initial portfolio implementation may allow registration for demo purposes. A production system may restrict this to admin-created users.

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

## User Endpoints

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
  "is_active": true
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

## Expense Endpoints

### Create Expense

```text
POST /api/v1/expenses
```

Required role: authenticated user.

Request:

```json
{
  "title": "Client lunch",
  "description": "Lunch with client after project meeting.",
  "category": "meals",
  "amount": 45.75,
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
  "created_at": "2026-06-19T05:00:00Z",
  "updated_at": "2026-06-19T05:00:00Z"
}
```

### List Expenses

```text
GET /api/v1/expenses
```

Required role: authenticated user.

Visibility:

- Employees see their own expenses.
- Managers see eligible team or assigned expenses.
- Accountants see expenses relevant to accounting review and payment.
- Admins see all expenses.

Query parameters:

- `status`
- `category`
- `requester_id`
- `from_date`
- `to_date`
- `limit`
- `offset`

### Get Expense

```text
GET /api/v1/expenses/{expense_id}
```

Required role: authenticated user with ownership or role-based access.

### Update Expense

```text
PATCH /api/v1/expenses/{expense_id}
```

Required role: requester or admin.

Allowed only when status is `draft` or `returned_to_employee`.

### Submit Expense

```text
POST /api/v1/expenses/{expense_id}/submit
```

Required role: requester or admin.

Allowed statuses:

- `draft`
- `returned_to_employee`

Resulting status:

- `submitted`

### Cancel Expense

```text
POST /api/v1/expenses/{expense_id}/cancel
```

Required role: requester or admin.

Allowed before accounting approval or payment.

Request:

```json
{
  "reason": "Submitted by mistake."
}
```

## Manager Approval Endpoints

### Approve Expense

```text
POST /api/v1/expenses/{expense_id}/manager-approval
```

Required role: `manager` or `admin`

Allowed status:

- `submitted`

Request:

```json
{
  "comment": "Approved for client meeting."
}
```

Resulting status:

- `manager_approved`

### Reject Expense As Manager

```text
POST /api/v1/expenses/{expense_id}/manager-rejection
```

Required role: `manager` or `admin`

Allowed status:

- `submitted`

Request:

```json
{
  "reason": "Receipt does not match submitted amount."
}
```

Resulting status:

- `manager_rejected`

### Return Expense To Employee

```text
POST /api/v1/expenses/{expense_id}/return-to-employee
```

Required role: `manager`, `accountant`, or `admin`

Allowed statuses:

- `submitted`
- `manager_approved`

Request:

```json
{
  "reason": "Please attach a clearer receipt."
}
```

Resulting status:

- `returned_to_employee`

## Accounting Endpoints

### Approve Expense For Payment

```text
POST /api/v1/expenses/{expense_id}/accounting-approval
```

Required role: `accountant` or `admin`

Allowed status:

- `manager_approved`

Request:

```json
{
  "comment": "Receipt and policy checks completed."
}
```

Resulting status:

- `accountant_approved`

### Reject Expense As Accountant

```text
POST /api/v1/expenses/{expense_id}/accounting-rejection
```

Required role: `accountant` or `admin`

Allowed status:

- `manager_approved`

Request:

```json
{
  "reason": "Expense is outside reimbursable policy."
}
```

Resulting status:

- `accountant_rejected`

## Payment Endpoints

### Mark Payment Pending

```text
POST /api/v1/expenses/{expense_id}/payment-pending
```

Required role: `accountant` or `admin`

Allowed status:

- `accountant_approved`

Request:

```json
{
  "payment_method": "bank_transfer",
  "notes": "Scheduled in weekly payment batch."
}
```

Resulting status:

- `payment_pending`

### Mark Expense Paid

```text
POST /api/v1/expenses/{expense_id}/paid
```

Required role: `accountant` or `admin`

Allowed status:

- `payment_pending`
- `accountant_approved`

Request:

```json
{
  "paid_at": "2026-06-19T05:00:00Z",
  "payment_method": "bank_transfer",
  "payment_reference": "BANK-REF-123",
  "notes": "Paid in June reimbursement batch."
}
```

Resulting status:

- `paid`

## Audit Endpoints

### Get Expense Audit History

```text
GET /api/v1/expenses/{expense_id}/audit-log
```

Required role: authenticated user with access to the expense.

Response:

```json
{
  "items": [
    {
      "id": "audit-id",
      "expense_id": "expense-id",
      "actor_id": "user-id",
      "previous_status": "submitted",
      "new_status": "manager_approved",
      "comment": "Approved for client meeting.",
      "created_at": "2026-06-19T05:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## Suggested Expense Categories

- `travel`
- `meals`
- `lodging`
- `office_supplies`
- `software`
- `training`
- `transportation`
- `other`

## Suggested Payment Methods

- `bank_transfer`
- `cash`
- `company_card`
- `check`
- `other`

## Status Transition Summary

```text
draft -> submitted
returned_to_employee -> submitted
submitted -> manager_approved
submitted -> manager_rejected
submitted -> returned_to_employee
manager_approved -> accountant_approved
manager_approved -> accountant_rejected
manager_approved -> returned_to_employee
accountant_approved -> payment_pending
accountant_approved -> paid
payment_pending -> paid
draft -> cancelled
submitted -> cancelled
returned_to_employee -> cancelled
```

