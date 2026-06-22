# Spec: Manager Approval Workflow

## Status

`done`

## Problem Statement

Submitted expenses need a manager decision step before accounting review. Managers and admins must be able to approve, reject, or return submitted expenses, with every decision recorded.

## Scope

- Add manager approval endpoint: `POST /api/v1/expenses/{expense_id}/manager-approval`.
- Add manager rejection endpoint: `POST /api/v1/expenses/{expense_id}/manager-rejection`.
- Add return endpoint for manager-stage submissions: `POST /api/v1/expenses/{expense_id}/return-to-employee`.
- Persist manager decisions in `approval_decisions`.
- Create audit log entries for manager approval, manager rejection, and returns.
- Set `manager_decided_at` for manager approval and rejection.
- Allow admins to perform manager actions.
- Allow a manager to act only on an assigned expense.

## Out Of Scope

- Accounting review.
- Payment tracking.
- Audit history retrieval endpoint.
- File upload handling.

## Acceptance Criteria

- Submitted expenses can move to `manager_approved`, `manager_rejected`, or `returned_to_employee`.
- Manager actions reject invalid source statuses with `409`.
- Non-manager users cannot perform manager actions.
- Managers cannot act on expenses not assigned to them.
- Admins can perform manager actions on any submitted expense.
- Rejection and return requests require a reason.
- Manager approvals accept an optional comment.
- Approval decisions and audit logs are created for each transition.
