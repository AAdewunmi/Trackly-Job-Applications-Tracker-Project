#!/usr/bin/env bash
#
# Sprint 4 Day 2 console-only verification runbook for Trackly.
#
# Purpose:
# Verify the GitHub Actions CI workflow and local CI-parity quality gates from
# the Docker Compose web service. This runbook intentionally checks startup,
# PostgreSQL connectivity, migration readiness, schema preparation, linting,
# formatting, coverage configuration, Codecov wiring, and tests.
#
# Execution:
# chmod +x docs/sprint-runbook/sprint-4/sprint-4-day-2.sh
# ./docs/sprint-runbook/sprint-4/sprint-4-day-2.sh
#
# Expected Docker Compose project:
# trackly-job-applications-tracker-project
#
# Expected web container name prefix:
# trackly-job-applications-tracker-project-web
#
# Expected PostgreSQL image:
# postgres:16-alpine

set -Eeuo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"
EXPECTED_WEB_CONTAINER_PREFIX="${EXPECTED_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
EXPECTED_POSTGRES_IMAGE="${EXPECTED_POSTGRES_IMAGE:-postgres:16-alpine}"
CI_WORKFLOW_FILE="${CI_WORKFLOW_FILE:-.github/workflows/ci.yml}"

export COMPOSE_PROJECT_NAME

print_section() {
  printf '\n==> %s\n\n' "$1"
}

print_command() {
  printf '$'
  printf ' %q' "$@"
  printf '\n'
}

run() {
  print_command "$@"
  "$@"
}

compose() {
  docker compose -p "$COMPOSE_PROJECT_NAME" "$@"
}

compose_exec() {
  compose exec -T "$WEB_SERVICE" "$@"
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Required command missing: %s\n' "$command_name" >&2
    exit 1
  fi
}

require_file() {
  local file_path="$1"

  if [[ ! -f "$file_path" ]]; then
    printf 'Required file missing: %s\n' "$file_path" >&2
    exit 1
  fi
}

assert_file_contains() {
  local file_path="$1"
  local expected_text="$2"
  local label="$3"

  if ! grep -Fq -- "$expected_text" "$file_path"; then
    printf 'Missing expected %s in %s:\n%s\n' "$label" "$file_path" "$expected_text" >&2
    exit 1
  fi

  printf 'Verified %s in %s\n' "$label" "$file_path"
}

assert_file_matches() {
  local file_path="$1"
  local expected_regex="$2"
  local label="$3"

  if ! grep -Eq -- "$expected_regex" "$file_path"; then
    printf 'Missing expected %s in %s:\n%s\n' "$label" "$file_path" "$expected_regex" >&2
    exit 1
  fi

  printf 'Verified %s in %s\n' "$label" "$file_path"
}

get_container_id() {
  local service_name="$1"

  compose ps -q "$service_name"
}

assert_container_running() {
  local service_name="$1"
  local container_id

  container_id="$(get_container_id "$service_name")"

  if [[ -z "$container_id" ]]; then
    printf 'No container found for service: %s\n' "$service_name" >&2
    exit 1
  fi

  local running_state
  running_state="$(docker inspect --format '{{.State.Running}}' "$container_id")"

  if [[ "$running_state" != "true" ]]; then
    printf 'Container for service %s is not running.\n' "$service_name" >&2
    exit 1
  fi

  printf 'Container for service %s is running: %s\n' "$service_name" "$container_id"
}

assert_web_container_name() {
  local container_id
  container_id="$(get_container_id "$WEB_SERVICE")"

  local container_name
  container_name="$(docker inspect --format '{{.Name}}' "$container_id" | sed 's#^/##')"

  if [[ "$container_name" != "$EXPECTED_WEB_CONTAINER_PREFIX"* ]]; then
    printf 'Unexpected web container name.\n' >&2
    printf 'Expected prefix: %s\n' "$EXPECTED_WEB_CONTAINER_PREFIX" >&2
    printf 'Actual name: %s\n' "$container_name" >&2
    exit 1
  fi

  printf 'Web container name verified: %s\n' "$container_name"
}

assert_postgres_image() {
  local container_id
  container_id="$(get_container_id "$DB_SERVICE")"

  local configured_image
  configured_image="$(docker inspect --format '{{.Config.Image}}' "$container_id")"

  if [[ "$configured_image" != "$EXPECTED_POSTGRES_IMAGE" ]]; then
    printf 'Unexpected PostgreSQL image.\n' >&2
    printf 'Expected: %s\n' "$EXPECTED_POSTGRES_IMAGE" >&2
    printf 'Actual: %s\n' "$configured_image" >&2
    exit 1
  fi

  printf 'PostgreSQL image verified: %s\n' "$configured_image"
}

wait_for_postgres() {
  print_section "Wait for PostgreSQL healthcheck"

  local attempt
  for attempt in $(seq 1 30); do
    if compose exec -T "$DB_SERVICE" pg_isready \
      -U "${POSTGRES_USER:-trackly_user}" \
      -d "${POSTGRES_DB:-trackly}" >/dev/null 2>&1; then
      printf 'PostgreSQL is ready after %s attempt(s).\n' "$attempt"
      return 0
    fi

    printf 'PostgreSQL not ready yet, attempt %s/30...\n' "$attempt"
    sleep 2
  done

  printf 'PostgreSQL did not become ready in time.\n' >&2
  return 1
}

print_section "Verify repository root"

require_file "manage.py"
require_file "docker-compose.yml"
require_file "Dockerfile"
require_file "Makefile"
require_file "requirements.txt"
require_file "pyproject.toml"
require_file "pytest.ini"
require_file ".env.example"
require_file "README.md"
require_file "docs/ci.md"
require_file "$CI_WORKFLOW_FILE"

printf 'Repository root verified: %s\n' "$(pwd)"

print_section "Verify required local commands"

require_command "docker"
require_command "grep"
require_command "sed"

run docker --version
run docker compose version

print_section "Verify CI workflow contract"

assert_file_contains "$CI_WORKFLOW_FILE" "name: CI Pipeline" "CI workflow name"
assert_file_contains "$CI_WORKFLOW_FILE" "name: Lint, format, and test" "required GitHub check job name"
assert_file_contains "$CI_WORKFLOW_FILE" "uses: actions/checkout@v4" "checkout action"
assert_file_contains "$CI_WORKFLOW_FILE" "uses: actions/setup-python@v5" "Python setup action"
assert_file_contains "$CI_WORKFLOW_FILE" "python-version: \"3.12\"" "Python 3.12 CI runtime"
assert_file_contains "$CI_WORKFLOW_FILE" "postgres:16-alpine" "PostgreSQL 16 Alpine service image"
assert_file_contains "$CI_WORKFLOW_FILE" "DATABASE_URL:" "database URL configuration"
assert_file_contains "$CI_WORKFLOW_FILE" "DJANGO_SETTINGS_MODULE: config.settings.test" "test settings configuration"
assert_file_contains "$CI_WORKFLOW_FILE" "python -m pip install -r requirements.txt" "dependency installation"
assert_file_contains "$CI_WORKFLOW_FILE" "Verify Django startup settings and database connection" "startup and DB verification"
assert_file_contains "$CI_WORKFLOW_FILE" "python -m ruff check ." "Ruff quality gate"
assert_file_contains "$CI_WORKFLOW_FILE" "python -m black . --check" "Black formatting quality gate"
assert_file_contains "$CI_WORKFLOW_FILE" "python manage.py check --settings=config.settings.test" "Django system check"
assert_file_contains "$CI_WORKFLOW_FILE" "python manage.py makemigrations" "migration drift check"
assert_file_contains "$CI_WORKFLOW_FILE" "python manage.py migrate --noinput --settings=config.settings.test" "migration application"
assert_file_contains "$CI_WORKFLOW_FILE" "Verify prepared database schema" "schema preparation verification"
assert_file_contains "$CI_WORKFLOW_FILE" "python manage.py check --deploy --settings=config.settings.production" "production deploy check"
assert_file_contains "$CI_WORKFLOW_FILE" "python -m pytest" "pytest invocation"
assert_file_contains "$CI_WORKFLOW_FILE" "--ds=config.settings.test" "pytest test settings override"
assert_file_contains "$CI_WORKFLOW_FILE" "--cov=apps" "coverage source"
assert_file_contains "$CI_WORKFLOW_FILE" "codecovcli upload-process" "Codecov upload"

print_section "Verify quality tool and test configuration"

assert_file_contains "pyproject.toml" "[tool.black]" "Black configuration block"
assert_file_contains "pyproject.toml" "[tool.ruff]" "Ruff configuration block"
assert_file_contains "pyproject.toml" "[tool.coverage.run]" "coverage run configuration block"
assert_file_contains "pyproject.toml" "[tool.coverage.report]" "coverage report configuration block"
assert_file_matches "pyproject.toml" "line-length[[:space:]]*=[[:space:]]*88" "shared line length"
assert_file_contains "pyproject.toml" "branch = true" "branch coverage"
assert_file_contains "pyproject.toml" "source = [\"apps\"]" "coverage source"
assert_file_contains "pyproject.toml" "fail_under = 95" "coverage threshold"
assert_file_contains "pytest.ini" "DJANGO_SETTINGS_MODULE = config.settings.test" "pytest Django settings"
assert_file_contains "pytest.ini" "apps" "app test discovery"
assert_file_contains "pytest.ini" "config" "config test discovery"
assert_file_contains "pytest.ini" "--reuse-db" "database reuse test option"

print_section "Verify CI documentation and README expectations"

assert_file_contains "docs/ci.md" "CI Pipeline / Lint, format, and test" "required check documentation"
assert_file_contains "docs/ci.md" "PostgreSQL 16" "PostgreSQL service documentation"
assert_file_contains "docs/ci.md" "Django startup settings import and connect to PostgreSQL" "startup documentation"
assert_file_contains "docs/ci.md" "Migration files match models" "migration check documentation"
assert_file_contains "docs/ci.md" "prepared database schema" "schema preparation documentation"
assert_file_contains "docs/ci.md" "Coverage policy is owned by" "coverage configuration documentation"
assert_file_contains "docs/ci.md" "Codecov" "Codecov documentation"
assert_file_contains "README.md" "[![Build]" "README build badge placeholder"
assert_file_contains "README.md" "![Tests]" "README tests badge placeholder"
assert_file_contains "README.md" "![Python]" "README Python badge placeholder"
assert_file_contains "README.md" "![Django]" "README Django badge placeholder"
assert_file_contains "README.md" "![Docker]" "README Docker badge placeholder"
assert_file_contains "README.md" "![Code Style]" "README code style badge placeholder"
assert_file_contains "README.md" "![Licence]" "README licence badge placeholder"
assert_file_contains "README.md" "CI Pipeline" "README CI section"
assert_file_contains "README.md" "configured coverage gate" "README pipeline expectation"

print_section "Start Docker Compose services"

run docker compose -p "$COMPOSE_PROJECT_NAME" up -d

print_section "Show Docker Compose service status"

run docker compose -p "$COMPOSE_PROJECT_NAME" ps

print_section "Verify required containers are running"

assert_container_running "$DB_SERVICE"
assert_container_running "$WEB_SERVICE"

print_section "Verify web container naming contract"

assert_web_container_name

print_section "Verify PostgreSQL service image"

assert_postgres_image

wait_for_postgres

print_section "Verify required commands inside web container"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "command -v python"
run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "command -v pytest"
run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "python -m ruff --version"
run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "python -m black --version"

print_section "Verify Django startup settings and PostgreSQL connection"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" \
  python manage.py shell \
  --settings=config.settings.test \
  -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor)"

print_section "Run Ruff quality gate"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python -m ruff check .

print_section "Run Black formatting quality gate"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python -m black . --check

print_section "Run Django system check for startup expectations"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" \
  python manage.py check --settings=config.settings.test

print_section "Verify migration files match models"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" \
  python manage.py makemigrations --check --dry-run --settings=config.settings.test

print_section "Apply migrations to prepare schema"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" \
  python manage.py migrate --noinput --settings=config.settings.test

print_section "Verify prepared database schema"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" \
  python manage.py shell \
  --settings=config.settings.test \
  -c "from django.db import connection; assert 'jobs_jobapplication' in connection.introspection.table_names()"

print_section "Run production deploy check"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T \
  -e DJANGO_SECRET_KEY=local-production-secret-key-with-enough-length-for-deploy-checks \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=trackly.example.com \
  -e DJANGO_CSRF_TRUSTED_ORIGINS=https://trackly.example.com \
  "$WEB_SERVICE" python manage.py check --deploy --settings=config.settings.production

print_section "Run CI-style pytest command with coverage"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" \
  python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml

print_section "Run CI-parity command sequence inside web container"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "
python -m ruff check . &&
python -m black . --check &&
python manage.py check --settings=config.settings.test &&
python manage.py makemigrations --check --dry-run --settings=config.settings.test &&
python manage.py migrate --noinput --settings=config.settings.test &&
python manage.py shell --settings=config.settings.test -c \"from django.db import connection; assert 'jobs_jobapplication' in connection.introspection.table_names()\" &&
python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml
"

print_section "Check Git working tree status"

run git status --short

print_section "Sprint 4 Day 2 verification complete"

printf 'Verified Docker Compose project: %s\n' "$COMPOSE_PROJECT_NAME"
printf 'Verified web service: %s\n' "$WEB_SERVICE"
printf 'Verified web container prefix: %s\n' "$EXPECTED_WEB_CONTAINER_PREFIX"
printf 'Verified PostgreSQL image: %s\n' "$EXPECTED_POSTGRES_IMAGE"
printf 'Verified CI workflow file: %s\n' "$CI_WORKFLOW_FILE"
printf 'Verified quality gates: Ruff, Black, Django startup check, migrations, schema preparation, production deploy check, pytest coverage, Codecov wiring.\n'
printf 'Sprint 4 Day 2 CI and automated quality gate baseline passed.\n'
