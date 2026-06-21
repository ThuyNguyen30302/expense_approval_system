# Expense Approval System

FastAPI backend for company expense request approval and payment tracking.

## Local Development

Install the project in a virtual environment, then run tests:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
```

Start the API and PostgreSQL with Docker Compose:

```powershell
docker compose up --build
```

## Development Admin Bootstrap

Self-service registration stays employee-only:

```text
POST /api/v1/auth/register
```

For development/demo usage, create the first admin with the CLI after migrations have been applied:

```powershell
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m app.cli seed-admin --email admin@example.com --password "change-me-admin" --full-name "Demo Admin"
```

If the email already exists, the command updates that user, promotes them to `admin`, reactivates them, and replaces the password. The command refuses to run when `APP_ENV=production`.

After installing the package, the equivalent console command is:

```powershell
expense-approval seed-admin --email admin@example.com --password "change-me-admin" --full-name "Demo Admin"
```

## Authentication

Login remains JSON-only:

```text
POST /api/v1/auth/login
```

Protected endpoints use HTTP Bearer tokens:

```text
Authorization: Bearer <access_token>
```
