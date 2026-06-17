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

Seed deterministic showcase demo data:

```bash
make seed
```

The seed command creates baseline roles, demo users, applications across every
workflow status, application notes, target role profiles, and persisted
retrieval-style insights generated through the current NLP service. It is
idempotent and intended only for local development, screenshots, manual QA, and
reviewer walkthroughs.

Demo accounts use the password `TracklyDemoPass123`:

- `admin.demo@trackly.local`
- `user.demo@trackly.local`
- `analyst.demo@trackly.local`
- `empty.demo@trackly.local`

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
checkpoints. Use the Sprint 3 Day 5 script as the current Sprint 3 completion
check:

```bash
./docs/sprint-runbook/sprint-3/sprint-3-day-5.sh
```

It verifies the Docker Compose project name, the web container, PostgreSQL,
migrations, insight browser routes, secured insight API routes, authentication
and ownership boundaries, NLTK preprocessing, TF-IDF cosine scoring,
explainability fields, idempotency, formatting, linting, focused insight tests,
and the full regression suite.

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

Render deployment is defined by the root `render.yaml` blueprint. It creates:

- `trackly-web` Docker web service
- `trackly-db` managed PostgreSQL database
- `DATABASE_URL` wired from `trackly-db`
- `/health/` as the Render health check path

The blueprint also runs migrations, collects static files, and starts Gunicorn
with `config.settings.production`.

Set or confirm these production values through Render environment variables or
the deployment secret store:

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `RELEASE_VERSION`

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
- `LOG_LEVEL`
- `DJANGO_LOG_LEVEL`

Before deployment, run:

```bash
make check
```

After deployment, run a smoke check against the deployed service:

```bash
curl -fsS https://<your-render-service>.onrender.com/health/
```

The response should include `status`, `service`, `release`, and `timestamp`.

For operational review, use Render logs with the release marker emitted by
production logging:

- Confirm `/health/` reports the expected `release`
- Filter service logs for `release=<release>`
- Use `LOG_LEVEL` for application verbosity
- Use `DJANGO_LOG_LEVEL` for Django framework verbosity

## Troubleshooting

If the web service cannot connect to the database, verify:

- Docker Compose is running both `web` and `db`
- `POSTGRES_HOST=db` for local Docker development
- `POSTGRES_PORT=5432`
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` match between the
  web and database services
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` match the values used
  when the local PostgreSQL volume was initialized
- In Render, `DATABASE_URL` is populated from the `trackly-db` managed database
  declared in `render.yaml`

If static files or deploy checks fail, run:

```bash
make deploy-check
```

If tests fail because services are not running, start them first:

```bash
make up
```

If local screenshots or manual QA need representative records, run:

```bash
make seed
```

Then run tests from another terminal:

```bash
make test
```

If cached Python or test files cause local noise, clean them:

```bash
make clean
```
