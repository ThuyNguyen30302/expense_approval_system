# Spec: Accounting Review And Payment Tracking

## Status

`done`

## Problem Statement

Manager-approved expenses need accounting review and payment tracking before the workflow is complete.

## Scope

- Add accounting approval endpoint.
- Add accounting rejection endpoint.
- Extend return-to-employee to allow accounting returns from `manager_approved`.
- Add payment pending endpoint.
- Add paid endpoint.
- Persist accounting decisions in `approval_decisions`.
- Persist payment actions in `payments`.
- Create audit log entries for all accounting and payment transitions.
- Set `accountant_decided_at`, `paid_at`, and payment metadata when applicable.

## Out Of Scope

- External payment provider integration.
- Payment file exports.
- Editing payment records after creation.

## Acceptance Criteria

- Accountants and admins can approve or reject manager-approved expenses.
- Accountants and admins can return manager-approved expenses to employees.
- Accountants and admins can mark accountant-approved expenses as payment pending.
- Accountants and admins can mark accountant-approved or payment-pending expenses as paid.
- Payment records are persisted for pending and paid actions.
- Reasons are required for rejection and return.
- Invalid transitions return `409`.
