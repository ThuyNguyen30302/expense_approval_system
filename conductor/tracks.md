# Tracks

This file tracks project work using a Conductor-inspired workflow.

## Status Legend

- `proposed`: Idea captured, not planned yet.
- `planned`: Spec and plan are ready.
- `approved`: Ready to implement after user approval.
- `in_progress`: Implementation is underway.
- `blocked`: Waiting for input or external dependency.
- `implemented`: Code is complete.
- `verified`: Tests and checks passed.
- `reviewed`: Review completed.
- `done`: Track is complete.

## Active Tracks

| Track ID | Title | Type | Status | Notes |
| --- | --- | --- | --- | --- |

## Proposed Tracks

| Track ID | Title | Type | Status | Notes |
| --- | --- | --- | --- | --- |
| `track-004-manager-approval` | Manager approval workflow | feature | proposed | Implement manager approve, reject, and return actions with audit logs. |
| `track-005-accounting-payment` | Accounting review and payment tracking | feature | proposed | Implement accountant approval, rejection, payment pending, and paid transitions. |
| `track-006-audit-history` | Audit history API | feature | proposed | Expose expense audit log retrieval and ensure status transitions are recorded. |
| `track-007-test-hardening` | Workflow and authorization test hardening | quality | proposed | Add end-to-end API workflow tests and role boundary coverage. |

## Completed Tracks

| Track ID | Title | Type | Status | Notes |
| --- | --- | --- | --- | --- |
| `track-001-project-scaffold` | Project scaffold and tooling | feature | done | FastAPI scaffold, PostgreSQL config, DB infrastructure, Alembic foundation, Docker setup, and smoke tests completed. |
| `track-002-auth-users` | Authentication and user management | feature | done | Auth, user management, reusable role dependencies, dev admin bootstrap, tests, and review follow-ups completed. |
| `track-003-expense-core` | Expense request core workflow | feature | done | Expense core workflow, receipt metadata, audit logging, PostgreSQL JSONB metadata, and verification completed. |
