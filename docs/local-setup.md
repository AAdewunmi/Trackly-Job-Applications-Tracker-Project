# Local Setup

## Purpose

This document describes how to run Trackly locally using Docker Compose,
Django, and PostgreSQL.

## Requirements

Install:

- Docker
- Docker Compose
- Make, optional but recommended

No local Python or PostgreSQL installation is required when using the container
workflow.

## Environment File

Create a local environment file from the tracked example:

```bash
cp .env.example .env
```

The `.env` file is ignored by git. Keep real local secrets and database
passwords there, not in committed files.

For local Docker development, use these settings:

```env
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

Set `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD` to local-only values. They do
not need to match production values.

If `POSTGRES_PASSWORD`, `POSTGRES_USER`, or `POSTGRES_DB` are changed after the
PostgreSQL volume has already been created, recreate the local database volume
or restore the values that were used when the volume was initialised.

## Start Services

Start the web and database services:

```bash
make up
```

Or use Docker Compose directly:

```bash
docker compose up
```

The Django app runs at:

```text
http://localhost:8000
```

The local PostgreSQL container exposes port `5432`.

## Database Setup

Apply migrations after the services are running:

```bash
make migrate
```

Or:

```bash
docker compose exec web python manage.py migrate
```

Create a superuser when needed:

```bash
make superuser
```

## Common Commands

```bash
make help
make build
make up
make down
make logs
make shell
make dbshell
make migrate
make migrations
make superuser
```

## Quality Checks

Run the test suite:

```bash
make test
```

Run linting:

```bash
make lint
```

Format code:

```bash
make format
```

Run the full local check target:

```bash
make check
```

The `check` target runs Ruff, Black format checks, migration checks, Django's
production deploy check, and pytest.

To run the completed Sprint 2 end-to-end verification script:

```bash
./docs/sprint-runbook/sprint-2/sprint-2-day-5.sh
```

Earlier sprint scripts are incremental checkpoint runbooks. See
`docs/sprint-runbook/README.md` before using them as current validation.

## Settings Modules

Trackly uses split Django settings:

- `config.settings.local` for local Docker development
- `config.settings.test` for pytest and CI
- `config.settings.production` for ASGI/WSGI deployment

Docker Compose runs the web service with `config.settings.local`.

## Stopping Services

Stop the containers:

```bash
make down
```

Or:

```bash
docker compose down
```
