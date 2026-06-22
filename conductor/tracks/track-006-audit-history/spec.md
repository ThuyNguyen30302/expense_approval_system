# Spec: Audit History API

## Status

`done`

## Problem Statement

Expense status changes and receipt events are already written to audit logs, but clients need a documented API to retrieve that history.

## Scope

- Add `GET /api/v1/expenses/{expense_id}/audit-log`.
- Return paginated audit rows ordered by creation time.
- Reuse expense access rules for requester, assigned manager, accountant-relevant statuses, and admin.
- Include event type, status changes, comment, metadata, actor, and timestamp.

## Out Of Scope

- Editing or deleting audit logs.
- Global audit search.
- Actor expansion beyond actor ID.

## Acceptance Criteria

- Authorized users can retrieve audit history for visible expenses.
- Unauthorized users receive `403`.
- Missing expenses return `404`.
- Pagination limit and offset are enforced.
- Workflow transitions appear in chronological audit output.
