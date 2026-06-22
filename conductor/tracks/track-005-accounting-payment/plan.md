# Plan: Accounting Review And Payment Tracking

## Status

`done`

## Implementation Phases

- [x] Confirm endpoint names and transition rules from `api-design.md`.
- [x] Add payment model, repository, schemas, and migration support.
- [x] Add accounting approval, rejection, and return service methods.
- [x] Add payment pending and paid service methods.
- [x] Add expense routes for accounting and payment actions.
- [x] Add authorization checks for accountant and admin roles.
- [x] Add tests for accounting, payment, invalid transitions, and forbidden users.
- [x] Run full verification.
- [x] Mark track done after review follow-ups.

## Definition Of Done

- [x] Accounting workflow endpoints are implemented.
- [x] Payment endpoints are implemented.
- [x] Approval decision and payment records are persisted.
- [x] Audit logs are written for each transition.
- [x] Tests cover success and failure cases.
- [x] Track status is `done`.
