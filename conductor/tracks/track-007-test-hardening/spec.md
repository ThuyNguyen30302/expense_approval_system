# Spec: Workflow And Authorization Test Hardening

## Status

`done`

## Problem Statement

The expense workflow now crosses requester, manager, accountant, and admin roles. The code needs test coverage that catches role leaks, invalid transitions, and Python-specific correctness issues.

## Scope

- Add end-to-end workflow tests from draft to paid.
- Add forbidden-role tests for manager, accounting, payment, and audit endpoints.
- Add invalid transition tests where gaps are found.
- Fix small code quality issues discovered during review.
- Keep route handlers thin and service-layer rules centralized.

## Out Of Scope

- Browser/frontend tests.
- Load testing.
- Full PostgreSQL test container conversion.

## Acceptance Criteria

- Full test suite passes.
- OpenAPI generation still works.
- Alembic offline SQL renders.
- Docker Compose config renders.
- Track 4, 5, 6, and 7 are all marked done.
