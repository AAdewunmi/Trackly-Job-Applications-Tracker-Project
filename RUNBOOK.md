# Trackly Runbook

## Purpose

This runbook provides common operational commands for developing, validating,
and troubleshooting Trackly.

## Local Prerequisites

Install:

- Docker
- Docker Compose
- Make, optional but recommended

Create a local environment file:

```bash
cp .env.example .env
```

For local development, `.env` should use:

```env
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_DEBUG=True
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

Keep real secret values in `.env` or the deployment secret store. Do not commit
real secrets.

## Service Lifecycle

Build the Docker images:

```bash
make build
```

Start the application and database:

```bash
make up
```

Stop the services:

```bash
make down
```

Restart running services:

```bash
make restart
```

Follow web logs:

```bash
make logs
```

The local app runs at:

```text
http://localhost:8000
```

## Database Operations

Apply migrations:

```bash
make migrate
```

Create new migrations:

```bash
make migrations
```

Check for missing migrations:

```bash
make migrations-check
```

Open a database shell:

```bash
make dbshell
```

Create a superuser:

```bash
make superuser
```

## Application Shell

Open the Django shell:

```bash
make shell
```

Run a Django management command directly:

```bash
docker compose exec web python manage.py <command>
```

## Validation

Run tests:

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

Check formatting:

```bash
make format-check
```

Run the full validation target:

```bash
make check
```

The full check runs:

- Ruff
- Black format check
- Django migration check
- Django production deploy check
- pytest

If repeated local test runs encounter a stale PostgreSQL test database, pytest
is configured with `--reuse-db` so the existing `test_trackly` database is
reused instead of being dropped and recreated.

## NLP Runtime Data

The Docker image provisions required NLTK runtime data during build. If a local
container reports missing NLTK data, refresh the data inside the web container:

```bash
make nltk-data
```

## Sprint Verification

The executable scripts under `docs/sprint-runbook/` capture incremental sprint
checkpoints. Use the Sprint 3 Day 2 script as the current insights completion
check:

```bash
./docs/sprint-runbook/sprint-3/sprint-3-day-2.sh
```

It verifies the Docker Compose project name, the web container, PostgreSQL,
migrations, formatting, linting, insight models, NLTK preprocessing, TF-IDF
cosine scoring, explainability fields, idempotency, focused insights tests, and
the full regression suite.

See `docs/sprint-runbook/README.md` before running an earlier checkpoint script.

## Continuous Integration

GitHub Actions runs Ruff, Black, migration checks, Django's production deploy
check, and pytest against PostgreSQL. CI requires at least 95% branch coverage
for `apps` and uploads `coverage.xml` to Codecov.

## Settings Modules

Trackly uses split Django settings:

- `config.settings.local` for local Docker development
- `config.settings.test` for tests and CI
- `config.settings.production` for deployment

The Docker Compose web service runs with `config.settings.local`.

## Production Configuration Checklist

Set production values through the deployment environment or secret store:

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Production security defaults are controlled by:

- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`
- `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF`
- `DJANGO_X_FRAME_OPTIONS`
- `DJANGO_REFERRER_POLICY`

Before deployment, run:

```bash
make check
```

## Troubleshooting

If the web service cannot connect to the database, verify:

- Docker Compose is running both `web` and `db`
- `POSTGRES_HOST=db` for local Docker development
- `POSTGRES_PORT=5432`
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` match between the
  web and database services
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` match the values used
  when the local PostgreSQL volume was initialized

If static files or deploy checks fail, run:

```bash
make deploy-check
```

If tests fail because services are not running, start them first:

```bash
make up
```

Then run tests from another terminal:

```bash
make test
```

If cached Python or test files cause local noise, clean them:

```bash
make clean
```
