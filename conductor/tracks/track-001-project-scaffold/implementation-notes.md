# Implementation Notes: Project Scaffold

This note explains the scaffold from the perspective of someone coming from TypeScript.

## `pyproject.toml`

This file is closest to `package.json` plus parts of `tsconfig.json` and tool config.

It defines:

- Project name and version.
- Supported Python version.
- Runtime dependencies.
- Development dependencies.
- Pytest configuration.
- Python package discovery rules.

The package discovery section tells Python tooling that only `app*` is application code. Without that, setuptools sees `app`, `alembic`, and `conductor` as possible packages and refuses to guess.

## `.venv`

The `.venv` directory is the Python equivalent of a local dependency sandbox.

In TypeScript, dependencies live in `node_modules`. In Python, dependencies are installed into a virtual environment so this project does not pollute the global Python installation.

Use:

```text
.\.venv\Scripts\python -m pytest
```

instead of plain:

```text
python -m pytest
```

because plain `python` on this machine points to Python 3.8, while this project uses Python 3.12.

## `app/main.py`

This is the FastAPI application entrypoint.

TypeScript mental model:

- Similar to `src/main.ts` in NestJS.
- Similar to the file where an Express app is created and routes are attached.

It creates:

```python
app = FastAPI(...)
```

Uvicorn imports this as:

```text
app.main:app
```

That means:

- `app.main` = Python module path `app/main.py`
- `app` after the colon = the FastAPI instance variable

## `GET /health`

This is a minimal smoke-test endpoint.

It proves:

- The app can import.
- FastAPI can route requests.
- TestClient can call the API.
- Uvicorn can serve the app.

It is intentionally not under `/api/v1` because it is infrastructure-level health, not a business API.

## `app/core/config.py`

This is the typed configuration layer.

TypeScript mental model:

- Similar to a typed `config.ts`.
- Similar to NestJS ConfigModule with schema validation.

It uses Pydantic Settings to read environment variables from:

- Real environment variables.
- `.env` if present.
- Defaults inside the settings class.

The `@lru_cache` wrapper means settings are created once and reused, instead of reparsed on every import.

## `app/db/base.py`

This file defines the SQLAlchemy declarative base.

Future SQLAlchemy models will inherit from this base. For now, it has no tables, which is expected for this scaffold track.

TypeScript mental model:

- Similar to establishing the base ORM registry before defining entities in TypeORM or Prisma models.

## `app/db/session.py`

This file creates:

- SQLAlchemy engine.
- Session factory.
- FastAPI-compatible database session dependency.

TypeScript mental model:

- Similar to creating a database client/provider that later services can inject.

No actual query runs at import time. The connection is used when a DB session is requested.

## Alembic Files

Alembic is the migration tool.

TypeScript mental model:

- Similar to Prisma migrations or TypeORM migrations.

Files added:

- `alembic.ini`: top-level Alembic config.
- `alembic/env.py`: runtime migration environment.
- `alembic/script.py.mako`: template for future migration files.
- `alembic/versions/.gitkeep`: keeps the empty versions directory in Git.

No migration was created because this track does not add business tables yet.

## `Dockerfile`

Defines how to build the API container.

It:

- Uses Python 3.11 slim.
- Installs dependencies from `pyproject.toml`.
- Copies the project files.
- Starts Uvicorn on port 8000.

## `docker-compose.yml`

Defines local development services:

- `api`: FastAPI backend.
- `db`: PostgreSQL.

It uses `.env.example` so the first `docker compose config` works even before a private `.env` file exists.

## `.env.example`

This documents local environment variables.

TypeScript mental model:

- Same purpose as `.env.example` in Node projects.

Real secrets should go in `.env`, which is ignored by Git.

PostgreSQL connection values for DBeaver Community are:

```text
Host: localhost
Port: 5432
Database: expense_approval
Username: expense_user
Password: expense_password
```

## `tests/test_health.py`

This file contains smoke tests.

It checks:

- The app imports.
- `/health` returns HTTP 200.
- `/health` returns `{"status": "ok"}`.

This is intentionally small. The next tracks will add real domain tests.
