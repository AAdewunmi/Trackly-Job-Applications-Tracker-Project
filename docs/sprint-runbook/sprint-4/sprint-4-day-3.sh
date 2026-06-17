#!/usr/bin/env bash
#
# Sprint 4 Day 3 console-only verification runbook for Trackly.
#
# Purpose:
# Verify the current production deployment baseline:
# - strict production settings environment contract
# - Render blueprint and managed PostgreSQL wiring
# - /health/ operational endpoint
# - production static collection with WhiteNoise storage
# - release-aware production logging
# - PostgreSQL runtime connectivity from Docker Compose
# - focused health and production-settings regression tests
# - final CI-quality gates from the Docker Compose web service
#
# Execution:
# chmod +x docs/sprint-runbook/sprint-4/sprint-4-day-3.sh
# ./docs/sprint-runbook/sprint-4/sprint-4-day-3.sh
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

PRODUCTION_SETTINGS="${PRODUCTION_SETTINGS:-config.settings.production}"
PRODUCTION_HOST="${PRODUCTION_HOST:-trackly.example.com}"
PRODUCTION_ORIGIN="${PRODUCTION_ORIGIN:-https://trackly.example.com}"
PRODUCTION_SECRET_KEY="${PRODUCTION_SECRET_KEY:-local-production-secret-key-with-enough-length-for-day-3-checks}"
PRODUCTION_DATABASE_URL="${PRODUCTION_DATABASE_URL:-postgres://trackly_user:trackly_password@db:5432/trackly}"
PRODUCTION_RELEASE_VERSION="${PRODUCTION_RELEASE_VERSION:-sprint-4-day-3-local}"
POSTGRES_READINESS_USER="${POSTGRES_READINESS_USER:-trackly_user}"
POSTGRES_READINESS_DB="${POSTGRES_READINESS_DB:-trackly}"
STATICFILES_GENERATED=0

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

cleanup_generated_staticfiles() {
  if [[ "$STATICFILES_GENERATED" == "1" && -d staticfiles ]]; then
    print_section "Clean generated collectstatic artifacts"
    run git clean -fdX staticfiles
    STATICFILES_GENERATED=0
  fi
}

trap cleanup_generated_staticfiles EXIT

production_exec() {
  compose exec -T \
    -e DJANGO_SECRET_KEY="$PRODUCTION_SECRET_KEY" \
    -e DJANGO_DEBUG=False \
    -e DJANGO_ALLOWED_HOSTS="$PRODUCTION_HOST" \
    -e DJANGO_CSRF_TRUSTED_ORIGINS="$PRODUCTION_ORIGIN" \
    -e DJANGO_SETTINGS_MODULE="$PRODUCTION_SETTINGS" \
    -e DATABASE_URL="$PRODUCTION_DATABASE_URL" \
    -e RELEASE_VERSION="$PRODUCTION_RELEASE_VERSION" \
    -e LOG_LEVEL=INFO \
    -e DJANGO_LOG_LEVEL=INFO \
    "$WEB_SERVICE" "$@"
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

require_text() {
  local file_path="$1"
  local expected_text="$2"
  local description="$3"

  if ! grep -Fq "$expected_text" "$file_path"; then
    printf 'Verification failed: %s\n' "$description" >&2
    printf 'File: %s\n' "$file_path" >&2
    printf 'Expected text: %s\n' "$expected_text" >&2
    exit 1
  fi

  printf 'Verified %s in %s\n' "$description" "$file_path"
}

require_any_text() {
  local file_path="$1"
  local description="$2"
  shift 2

  local expected_text

  for expected_text in "$@"; do
    if grep -Fq "$expected_text" "$file_path"; then
      printf 'Verified %s in %s\n' "$description" "$file_path"
      return 0
    fi
  done

  printf 'Verification failed: %s\n' "$description" >&2
  printf 'File: %s\n' "$file_path" >&2
  printf 'None of the expected text values were found.\n' >&2
  exit 1
}

first_existing_file() {
  local file_path

  for file_path in "$@"; do
    if [[ -f "$file_path" ]]; then
      printf '%s\n' "$file_path"
      return 0
    fi
  done

  return 1
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
  local attempt
  local max_attempts=30

  for attempt in $(seq 1 "$max_attempts"); do
    if compose exec -T "$DB_SERVICE" \
      pg_isready -U "$POSTGRES_READINESS_USER" -d "$POSTGRES_READINESS_DB" \
      >/dev/null 2>&1; then
      printf 'PostgreSQL is ready after %s attempt(s).\n' "$attempt"
      return 0
    fi

    sleep 1
  done

  printf 'PostgreSQL did not become ready after %s attempts.\n' "$max_attempts" >&2
  exit 1
}

print_section "Verify repository root"

require_file "manage.py"
require_file "docker-compose.yml"
require_file "Dockerfile"
require_file "Makefile"
require_file "requirements.txt"
require_file ".env.example"
require_file "README.md"
require_file "RUNBOOK.md"
require_file "render.yaml"
require_file "config/settings/base.py"
require_file "config/settings/production.py"
require_file "config/urls.py"
require_file "docs/deployment.md"
require_file "config/tests/test_health_check.py"
require_file "config/tests/test_production_settings.py"

printf 'Repository root verified: %s\n' "$(pwd)"

print_section "Verify required local commands"

require_command "docker"
require_command "git"

run docker --version
run docker compose version

print_section "Verify production settings file contract"

require_text "config/settings/production.py" "os.environ[\"DJANGO_SECRET_KEY\"]" "required production secret key"
require_text "config/settings/production.py" "DEBUG = False" "production debug disabled"
require_text "config/settings/production.py" "DJANGO_ALLOWED_HOSTS" "required production allowed hosts"
require_text "config/settings/production.py" "ImproperlyConfigured" "fail-fast allowed-host validation"
require_text "config/settings/production.py" "DJANGO_CSRF_TRUSTED_ORIGINS" "production CSRF trusted origins"
require_text "config/settings/production.py" "DATABASE_URL" "required database URL"
require_text "config/settings/production.py" "dj_database_url" "database URL parser"
require_text "config/settings/production.py" "SECURE_SSL_REDIRECT" "secure SSL redirect"
require_text "config/settings/production.py" "SESSION_COOKIE_SECURE" "secure session cookie"
require_text "config/settings/production.py" "CSRF_COOKIE_SECURE" "secure CSRF cookie"
require_text "config/settings/production.py" "SECURE_HSTS_SECONDS" "HSTS configuration"
require_text "config/settings/production.py" "ReleaseVersionFilter" "release logging filter"
require_text "config/settings/production.py" "release=%(release_version)s" "release-aware log format"
require_text "config/settings/production.py" "LOG_LEVEL" "root log level env control"
require_text "config/settings/production.py" "DJANGO_LOG_LEVEL" "Django log level env control"

print_section "Verify base settings static and WhiteNoise contract"

require_text "config/settings/base.py" "whitenoise.middleware.WhiteNoiseMiddleware" "WhiteNoise middleware"
require_text "config/settings/base.py" "STATIC_ROOT" "static root configuration"
require_text "config/settings/base.py" "CompressedManifestStaticFilesStorage" "compressed manifest static storage"
require_text "config/settings/base.py" "MEDIA_ROOT" "media root configuration"

print_section "Verify Render blueprint contract"

require_text "render.yaml" "name: trackly-web" "Render web service"
require_text "render.yaml" "runtime: docker" "Render Docker runtime"
require_text "render.yaml" "healthCheckPath: /health/" "Render health check path"
require_text "render.yaml" "gunicorn config.wsgi:application" "Render Gunicorn startup"
require_text "render.yaml" "collectstatic --noinput" "Render static collection"
require_text "render.yaml" "DATABASE_URL" "Render database URL env var"
require_text "render.yaml" "name: trackly-db" "Render managed database"
require_text "render.yaml" "DJANGO_ALLOWED_HOSTS" "Render allowed-host env var"
require_text "render.yaml" "DJANGO_CSRF_TRUSTED_ORIGINS" "Render CSRF origin env var"
require_text "render.yaml" "LOG_LEVEL" "Render root log level env var"
require_text "render.yaml" "DJANGO_LOG_LEVEL" "Render Django log level env var"

print_section "Verify health endpoint route contract"

require_text "config/urls.py" "path(\"health/\"" "health route registration"
require_text "config/urls.py" "JsonResponse" "JSON health response"
require_text "config/urls.py" "\"status\": \"ok\"" "health status payload"
require_text "config/urls.py" "\"release\"" "health release metadata"
require_text "config/urls.py" "\"timestamp\"" "health timestamp metadata"

print_section "Verify deployment documentation contract"

require_text "docs/deployment.md" "render.yaml" "Render blueprint documentation"
require_text "docs/deployment.md" "config.settings.production" "production settings documentation"
require_text "docs/deployment.md" "DATABASE_URL" "database URL documentation"
require_text "docs/deployment.md" "/health/" "health endpoint documentation"
require_text "docs/deployment.md" "collectstatic" "static collection documentation"
require_text "docs/deployment.md" "Logging And Operational Review" "logging documentation section"
require_text "docs/deployment.md" "release=<RELEASE_VERSION>" "release-aware logging documentation"
require_text "README.md" "render.yaml" "README Render blueprint documentation"
require_text "README.md" "release=<RELEASE_VERSION>" "README release-aware logging documentation"
require_text "RUNBOOK.md" "release=<release>" "runbook release log filtering guidance"

print_section "Verify environment example production variables"

require_text ".env.example" "DJANGO_SECRET_KEY" "production secret key example"
require_text ".env.example" "DJANGO_ALLOWED_HOSTS" "production allowed hosts example"
require_text ".env.example" "DJANGO_CSRF_TRUSTED_ORIGINS" "production CSRF trusted origins example"
require_text ".env.example" "DATABASE_URL" "database URL example"
require_text ".env.example" "LOG_LEVEL" "root log level example"
require_text ".env.example" "DJANGO_LOG_LEVEL" "Django log level example"

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

print_section "Wait for PostgreSQL healthcheck"

wait_for_postgres

print_section "Verify required commands inside web container"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "command -v python"
run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "command -v pytest"
run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "command -v gunicorn"

print_section "Verify production settings can import"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.conf import settings
print(settings.DEBUG)
print(settings.ALLOWED_HOSTS)
print(settings.DATABASES['default']['HOST'])
assert settings.DEBUG is False
assert '$PRODUCTION_HOST' in settings.ALLOWED_HOSTS
assert settings.RELEASE_VERSION == '$PRODUCTION_RELEASE_VERSION'
"

print_section "Run production deploy check"

run production_exec python manage.py check --deploy --settings="$PRODUCTION_SETTINGS"

print_section "Verify production PostgreSQL connection"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.db import connection
connection.ensure_connection()
print(connection.vendor)
assert connection.vendor == 'postgresql'
"

print_section "Verify production migrations can run"

run production_exec python manage.py migrate --noinput --settings="$PRODUCTION_SETTINGS"

print_section "Verify production schema is prepared"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.db import connection
tables = connection.introspection.table_names()
assert 'jobs_jobapplication' in tables
assert 'insights_jobinsight' in tables
print('PRODUCTION_SCHEMA_READY')
"

print_section "Collect static files with production settings"

STATICFILES_GENERATED=1
run production_exec python manage.py collectstatic --noinput --settings="$PRODUCTION_SETTINGS"

print_section "Verify static files were collected"

run compose_exec sh -lc "test -d staticfiles && find staticfiles -type f | head -n 5"

cleanup_generated_staticfiles

print_section "Verify health endpoint through Django test client under production settings"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.test import Client
response = Client().get('/health/', secure=True, HTTP_HOST='$PRODUCTION_HOST')
body = response.content.decode()
print(response.status_code)
print(body)
assert response.status_code == 200
assert 'ok' in body.lower()
assert '$PRODUCTION_RELEASE_VERSION' in body
"

print_section "Verify release-aware logging configuration loads under production settings"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
import logging
from django.conf import settings
assert isinstance(settings.LOGGING, dict)
assert 'release=%(release_version)s' in settings.LOGGING['formatters']['standard']['format']
logging.getLogger('django').info('TRACKLY_DAY_3_LOGGING_PROBE')
print('LOGGING_CONFIG_READY')
"

print_section "Run health-check tests"

HEALTH_TEST_FILE="$(first_existing_file \
  config/tests/test_health_check.py \
  tests/test_health_check.py \
  config/tests/test_health.py \
  config/tests/test_health_endpoint.py \
  apps/dashboard/tests/test_health_check.py \
  || true)"

if [[ -z "$HEALTH_TEST_FILE" ]]; then
  printf 'No health-check test file found.\n' >&2
  exit 1
fi

printf 'Health-check test file selected: %s\n' "$HEALTH_TEST_FILE"

run compose_exec pytest "$HEALTH_TEST_FILE" -q

print_section "Run focused production-readiness regression tests"

run compose_exec pytest config/tests/test_production_settings.py config/tests/test_health_check.py -q

print_section "Run final CI-quality gates for Day 3"

run compose_exec sh -lc "
python -m ruff check . &&
python -m black . --check &&
python manage.py check --settings=config.settings.test &&
python manage.py makemigrations --check --dry-run --settings=config.settings.test &&
python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml
"

print_section "Check Git working tree status"

run git status --short

print_section "Sprint 4 Day 3 verification complete"

printf 'Verified Docker Compose project: %s\n' "$COMPOSE_PROJECT_NAME"
printf 'Verified web service: %s\n' "$WEB_SERVICE"
printf 'Verified web container prefix: %s\n' "$EXPECTED_WEB_CONTAINER_PREFIX"
printf 'Verified PostgreSQL image: %s\n' "$EXPECTED_POSTGRES_IMAGE"
printf 'Verified production settings module: %s\n' "$PRODUCTION_SETTINGS"
printf 'Verified production host: %s\n' "$PRODUCTION_HOST"
printf 'Verified Render blueprint: render.yaml\n'
printf 'Verified production deploy check, PostgreSQL connection, migrations, static collection, health endpoint, and release-aware logging configuration.\n'
printf 'Sprint 4 Day 3 production deployment, health check, and logging baseline passed.\n'
