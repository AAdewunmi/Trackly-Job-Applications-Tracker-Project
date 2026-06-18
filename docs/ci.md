# Trackly CI Pipeline

Trackly uses GitHub Actions as the repository quality gate. The workflow lives
at:

```text
.github/workflows/ci.yml
```

The required GitHub status check is:

```text
CI Pipeline / Lint, format, and test
```

The job runs on Ubuntu with Python 3.12 and provisions a PostgreSQL 16 service
before running application checks.

## Triggers

CI runs for:

- Pull requests targeting `main` or `develop`
- Pushes to `main` and repository branches
- Manual `workflow_dispatch` runs

## Database

The workflow starts a `postgres:16-alpine` service with the same database
settings shape used by the Django app:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

CI points Django at the service through `config.settings.test` and verifies that
Django can open a real PostgreSQL connection before linting and tests run.

## Checks

The CI job verifies:

- Dependencies install from `requirements.txt`
- Django startup settings import and connect to PostgreSQL
- Ruff linting passes
- Black formatting check passes
- `manage.py check` passes with `config.settings.test`
- Migration files match models with `makemigrations --check --dry-run`
- Migrations apply with `migrate --noinput`
- The prepared database schema contains the expected application table
- Production deploy checks pass with `config.settings.production`
- Static files collect with `config.settings.production`
- The production settings contract required by `render.yaml` stays valid
- Pytest passes against the PostgreSQL-backed test settings

## Pipeline Expectations

Reviewers and contributors should treat a passing pipeline as proof that a
change can:

- Install the project from a clean checkout
- Start Django with the test settings module
- Connect to PostgreSQL instead of relying on an in-memory or local-only setup
- Keep model changes and migration files in sync
- Apply migrations and prepare the database schema
- Pass linting and formatting checks
- Pass the regression test suite with the configured coverage gate
- Satisfy the production deploy check for required security settings
- Verify production static-file collection before deployment
- Preserve the Render blueprint contract for required environment values,
  `DATABASE_URL`, and the `/health/` operational endpoint

## Test And Coverage Configuration

Pytest configuration is owned by `pytest.ini`. Test discovery includes:

- `apps`
- `config`

Coverage policy is owned by `pyproject.toml`:

- Branch coverage is enabled
- Coverage source is `apps`
- Minimum required coverage is `95%`

CI writes `coverage.xml` and uploads it to Codecov with `codecov-cli`.

## Local Equivalents

The closest local command set is:

```bash
make lint
make format-check
make migrations-check
make deploy-check
make test
```

For the CI-style PostgreSQL-backed test command:

```bash
docker compose exec web python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml
```

## Notes

The workflow intentionally validates startup and schema preparation, not only
isolated unit tests. This helps catch broken settings, missing migrations,
database connectivity problems, and production configuration regressions before
merge.

Hosted deployment is configured by the root `render.yaml` blueprint. CI does
not deploy to Render, but its production deploy check, production static-file
collection check, Render blueprint contract tests, and health endpoint tests
guard the same settings contract Render uses at runtime.
