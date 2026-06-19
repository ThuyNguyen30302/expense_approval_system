# Product Context

## Product Name

Expense Approval System

## Product Type

Backend API project for a company expense approval workflow.

## Project Intent

This is a personal portfolio backend project designed to demonstrate practical backend engineering skills using Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pydantic, JWT authentication, Pytest, and Docker.

The system manages expense requests from employee submission through manager approval, accountant review, and payment tracking.

## Primary Users

- Employees who submit expense reimbursement requests.
- Managers who approve, reject, or return submitted requests.
- Accountants who review approved requests and track payments.
- Admins who manage users and oversee the system.

## Product Goals

- Provide a clear expense request workflow from draft to paid.
- Enforce role-based access control.
- Maintain an auditable history of expense status transitions.
- Provide a clean REST API that is easy to test and document.
- Keep business rules explicit and centralized.
- Make the project easy to understand for recruiters, reviewers, and future maintainers.

## Core Capabilities

- JWT-based authentication.
- User and role management.
- Expense request creation, update, submission, and cancellation.
- Manager approval and rejection.
- Accountant review and rejection.
- Payment status tracking.
- Audit history for workflow transitions.
- API documentation through FastAPI OpenAPI.
- Automated tests with Pytest.
- Local development with Docker.

## Scope Boundaries

### In Scope

- Backend API only.
- Relational persistence for workflow state.
- PostgreSQL JSON/JSONB metadata where useful.
- Migrations with Alembic.
- Role and ownership authorization.
- Tests for core workflows.

### Out Of Scope For Initial Build

- Frontend UI.
- Real payment provider integration.
- Receipt image OCR.
- Email, Slack, or push notifications.
- Multi-tenant company isolation.

## Success Criteria

- A reviewer can understand the domain and architecture from documentation.
- The implementation can be built incrementally from specs and plans.
- The system demonstrates production-minded backend practices.
- Each implemented feature has clear tests and verification steps.
