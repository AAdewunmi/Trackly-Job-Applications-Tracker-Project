#!/usr/bin/env bash
#
# Sprint 4 Day 4 console-only verification runbook for Trackly.
#
# Purpose:
# Verify the current Render deployment readiness baseline after the Day 4
# Dockerfile and deployment-documentation updates:
# - Docker image build/start contract uses Gunicorn by default
# - Docker Compose keeps the local runserver override
# - Render blueprint defines a Docker web service and managed PostgreSQL
# - production settings require environment-driven secrets, hosts, and database URL
# - production runtime can check, migrate, collect static files, and load WSGI
# - health, account, dashboard, applications, insights, API auth, and static
#   contracts are smoke-checked locally under production settings
# - optional live Render URL checks can run after future deployment
#
# Execution:
# chmod +x docs/sprint-runbook/sprint-4/sprint-4-day-4.sh
# ./docs/sprint-runbook/sprint-4/sprint-4-day-4.sh
#
# Expected Docker Compose project:
# trackly-job-applications-tracker-project
#
# Expected web container name prefix:
# trackly-job-applications-tracker-project-web
#
# Expected PostgreSQL image:
# postgres:16-alpine
#
# Optional live verification after Render deployment:
# TRACKLY_LIVE_URL=https://your-render-url.onrender.com ./docs/sprint-runbook/sprint-4/sprint-4-day-4.sh
#
# Optional live API token verification:
# TRACKLY_LIVE_URL=https://your-render-url.onrender.com \
# TRACKLY_LIVE_EMAIL=reviewer@example.com \
# TRACKLY_LIVE_PASSWORD=secret \
# ./docs/sprint-runbook/sprint-4/sprint-4-day-4.sh
#
# Strict live verification:
# REQUIRE_LIVE_DEPLOYMENT=1 TRACKLY_LIVE_URL=https://your-render-url.onrender.com ./docs/sprint-runbook/sprint-4/sprint-4-day-4.sh

set -Eeuo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"
EXPECTED_WEB_CONTAINER_PREFIX="${EXPECTED_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
EXPECTED_POSTGRES_IMAGE="${EXPECTED_POSTGRES_IMAGE:-postgres:16-alpine}"

PRODUCTION_SETTINGS="${PRODUCTION_SETTINGS:-config.settings.production}"
PRODUCTION_HOST="${PRODUCTION_HOST:-trackly.example.com}"
PRODUCTION_ORIGIN="${PRODUCTION_ORIGIN:-https://trackly.example.com}"
PRODUCTION_SECRET_KEY="${PRODUCTION_SECRET_KEY:-local-production-secret-key-with-enough-length-for-day-4-checks}"
PRODUCTION_DATABASE_URL="${PRODUCTION_DATABASE_URL:-postgres://trackly_user:trackly_password@db:5432/trackly}"
PRODUCTION_RELEASE_VERSION="${PRODUCTION_RELEASE_VERSION:-sprint-4-day-4-local}"
POSTGRES_READINESS_USER="${POSTGRES_READINESS_USER:-trackly_user}"
POSTGRES_READINESS_DB="${POSTGRES_READINESS_DB:-trackly}"

TRACKLY_LIVE_URL="${TRACKLY_LIVE_URL:-}"
TRACKLY_LIVE_EMAIL="${TRACKLY_LIVE_EMAIL:-}"
TRACKLY_LIVE_PASSWORD="${TRACKLY_LIVE_PASSWORD:-}"
REQUIRE_LIVE_DEPLOYMENT="${REQUIRE_LIVE_DEPLOYMENT:-0}"

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

cleanup_generated_staticfiles() {
  if [[ "$STATICFILES_GENERATED" == "1" && -d staticfiles ]]; then
    print_section "Clean generated collectstatic artifacts"
    run git clean -fdX staticfiles
    STATICFILES_GENERATED=0
  fi
}

trap cleanup_generated_staticfiles EXIT

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

normalise_live_url() {
  local raw_url="$1"

  printf '%s' "$raw_url" | sed 's#/$##'
}

verify_live_url() {
  local live_url
  live_url="$(normalise_live_url "$TRACKLY_LIVE_URL")"

  print_section "Verify live Render URL"

  printf 'Live URL selected: %s\n' "$live_url"

  run curl --fail --silent --show-error --location "$live_url/health/"
  run curl --fail --silent --show-error --location "$live_url/" --output /tmp/trackly_home.html
  run test -s /tmp/trackly_home.html
  run curl --fail --silent --show-error --location "$live_url/accounts/signup/" --output /tmp/trackly_signup.html
  run test -s /tmp/trackly_signup.html
  run curl --fail --silent --show-error --location "$live_url/accounts/login/" --output /tmp/trackly_login.html
  run test -s /tmp/trackly_login.html
  run curl --fail --silent --show-error --location "$live_url/static/css/theme.css" --output /tmp/trackly_theme.css
  run test -s /tmp/trackly_theme.css

  print_section "Verify live secured API rejects unauthenticated requests"

  local status_code
  status_code="$(curl --silent --output /tmp/trackly_api_response.json --write-out '%{http_code}' "$live_url/api/v1/jobs/applications/")"

  printf 'Unauthenticated jobs API status: %s\n' "$status_code"

  if [[ "$status_code" != "401" && "$status_code" != "403" ]]; then
    printf 'Expected unauthenticated API request to return 401 or 403.\n' >&2
    printf 'Actual status: %s\n' "$status_code" >&2
    printf 'Response body:\n' >&2
    cat /tmp/trackly_api_response.json >&2
    exit 1
  fi

  if [[ -n "$TRACKLY_LIVE_EMAIL" && -n "$TRACKLY_LIVE_PASSWORD" ]]; then
    print_section "Verify live API token endpoint"

    status_code="$(
      curl --silent --output /tmp/trackly_token_response.json --write-out '%{http_code}' \
        --request POST \
        --header 'Content-Type: application/json' \
        --data "{\"email\":\"$TRACKLY_LIVE_EMAIL\",\"password\":\"$TRACKLY_LIVE_PASSWORD\"}" \
        "$live_url/api/v1/auth/token/"
    )"

    printf 'Token endpoint status: %s\n' "$status_code"

    if [[ "$status_code" != "200" ]]; then
      printf 'Expected token endpoint to return 200 for live test credentials.\n' >&2
      cat /tmp/trackly_token_response.json >&2
      exit 1
    fi
  else
    printf 'Live API token check skipped because TRACKLY_LIVE_EMAIL and TRACKLY_LIVE_PASSWORD are not set.\n'
  fi
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
require_file "config/tests/test_health_check.py"
require_file "config/tests/test_production_settings.py"
require_file "docs/deployment.md"

printf 'Repository root verified: %s\n' "$(pwd)"

print_section "Verify required local commands"

require_command "docker"
require_command "git"
require_command "curl"

run docker --version
run docker compose version
run git --version
run curl --version

print_section "Verify Dockerfile and Docker Compose runtime contract"

require_text "Dockerfile" "FROM python:3.12-slim" "Python 3.12 slim base image"
require_text "Dockerfile" "COPY requirements.txt" "dependency layer cache boundary"
require_text "Dockerfile" "pip install --no-cache-dir -r /app/requirements.txt" "predictable dependency installation"
require_text "Dockerfile" "python -m playwright install chromium" "Playwright runtime installation"
require_text "Dockerfile" "python -m nltk.downloader" "NLTK runtime data installation"
require_text "Dockerfile" "CMD [\"gunicorn\", \"config.wsgi:application\"" "Gunicorn default command"
require_text "docker-compose.yml" "command: python manage.py runserver" "local runserver override"
require_text "docker-compose.yml" "postgres:16-alpine" "local PostgreSQL image"

print_section "Verify production settings contract"

require_text "config/settings/production.py" "os.environ[\"DJANGO_SECRET_KEY\"]" "required production secret key"
require_text "config/settings/production.py" "DEBUG = False" "production debug disabled"
require_text "config/settings/production.py" "DJANGO_ALLOWED_HOSTS" "required production allowed hosts"
require_text "config/settings/production.py" "ImproperlyConfigured" "fail-fast allowed-host validation"
require_text "config/settings/production.py" "DJANGO_CSRF_TRUSTED_ORIGINS" "production CSRF trusted origins"
require_text "config/settings/production.py" "DATABASE_URL" "required database URL"
require_text "config/settings/production.py" "dj_database_url" "database URL parser"
require_text "config/settings/production.py" "ReleaseVersionFilter" "release logging filter"
require_text "config/settings/production.py" "release=%(release_version)s" "release-aware log format"
require_text "config/settings/production.py" "LOG_LEVEL" "root log level env control"
require_text "config/settings/production.py" "DJANGO_LOG_LEVEL" "Django log level env control"

print_section "Verify static file and WhiteNoise contract"

require_text "config/settings/base.py" "whitenoise.middleware.WhiteNoiseMiddleware" "WhiteNoise middleware"
require_text "config/settings/base.py" "STATIC_ROOT" "static root configuration"
require_text "config/settings/base.py" "CompressedManifestStaticFilesStorage" "compressed manifest static storage"
require_text "config/settings/base.py" "MEDIA_ROOT" "media root configuration"

print_section "Verify Render blueprint contract"

require_text "render.yaml" "name: trackly-web" "Render web service"
require_text "render.yaml" "runtime: docker" "Render Docker runtime"
require_text "render.yaml" "dockerfilePath: ./Dockerfile" "Render Dockerfile path"
require_text "render.yaml" "dockerCommand:" "Render production startup override"
require_text "render.yaml" "migrate --noinput" "Render migration command"
require_text "render.yaml" "collectstatic --noinput" "Render static collection command"
require_text "render.yaml" "gunicorn config.wsgi:application" "Render Gunicorn startup"
require_text "render.yaml" "healthCheckPath: /health/" "Render health check path"
require_text "render.yaml" "DATABASE_URL" "Render database URL env var"
require_text "render.yaml" "name: trackly-db" "Render managed database"
require_text "render.yaml" "DJANGO_ALLOWED_HOSTS" "Render allowed-host env var"
require_text "render.yaml" "DJANGO_CSRF_TRUSTED_ORIGINS" "Render CSRF origin env var"
require_text "render.yaml" "LOG_LEVEL" "Render root log level env var"
require_text "render.yaml" "DJANGO_LOG_LEVEL" "Render Django log level env var"

print_section "Verify product URL contract"

require_text "config/urls.py" "path(\"health/\"" "health route registration"
require_text "config/urls.py" "path(\"accounts/\"" "accounts route registration"
require_text "config/urls.py" "path(\"applications/\"" "applications route registration"
require_text "config/urls.py" "path(\"dashboard/\"" "dashboard route registration"
require_text "config/urls.py" "path(\"insights/\"" "insights route registration"
require_text "config/urls.py" "api/v1/auth/token/" "API token route registration"

print_section "Verify deployment documentation contract"

require_text "docs/deployment.md" "Deployment Choices And Growth Path" "deployment tradeoff documentation"
require_text "docs/deployment.md" "Render Blueprint is used because" "Render rationale documentation"
require_text "docs/deployment.md" "Docker is used" "Docker rationale documentation"
require_text "docs/deployment.md" "Managed PostgreSQL is used" "database rationale documentation"
require_text "docs/deployment.md" "WhiteNoise is enough" "static-file rationale documentation"
require_text "docs/deployment.md" "As the product grows, revisit" "growth path documentation"
require_text "docs/deployment.md" "Post-Deploy Product Smoke Checks" "post-deploy smoke checklist"
require_text "docs/deployment.md" "/accounts/signup/" "signup smoke check"
require_text "docs/deployment.md" "/accounts/login/" "login smoke check"
require_text "docs/deployment.md" "/applications/" "applications smoke check"
require_text "docs/deployment.md" "/api/v1/auth/token/" "API token smoke check"
require_text "README.md" "post-deploy product smoke checklist" "README smoke checklist pointer"

print_section "Verify environment example contract"

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

run compose_exec sh -lc "command -v python"
run compose_exec sh -lc "command -v pytest"
run compose_exec sh -lc "command -v gunicorn"

print_section "Run full test suite before release verification"

run compose_exec python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml

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

print_section "Seed and verify production roles"

run production_exec python manage.py seed_roles --settings="$PRODUCTION_SETTINGS"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.db import connection
from apps.roles.models import Role

tables = connection.introspection.table_names()
roles = sorted(Role.objects.values_list('code', flat=True))

print('PRODUCTION_TABLES_READY=', 'jobs_jobapplication' in tables and 'insights_jobinsight' in tables)
print('ROLES=', roles)

assert 'jobs_jobapplication' in tables
assert 'insights_jobinsight' in tables
assert 'admin' in roles
assert 'member' in roles
"

print_section "Collect static files with production settings"

STATICFILES_GENERATED=1
run production_exec python manage.py collectstatic --noinput --settings="$PRODUCTION_SETTINGS"

print_section "Verify static files were collected"

run compose_exec sh -lc "test -d staticfiles && test -f staticfiles/css/theme.css && find staticfiles -type f | head -n 10"

cleanup_generated_staticfiles

print_section "Verify Gunicorn can import production WSGI application"

run production_exec sh -lc "gunicorn config.wsgi:application --check-config"

print_section "Verify production health endpoint with test client"

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

print_section "Verify production product routes and API auth with test client"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.contrib.auth import get_user_model
from django.test import Client

from apps.jobs.models import JobApplication

User = get_user_model()
email = 'sprint4-day4-smoke@trackly.local'
password = 'TracklySmokePass123'
user, _ = User.objects.update_or_create(
    email=email,
    defaults={'first_name': 'Sprint', 'last_name': 'Smoke', 'is_active': True},
)
user.set_password(password)
user.save()

client = Client(HTTP_HOST='$PRODUCTION_HOST')

public_routes = {
    '/': 200,
    '/accounts/signup/': 200,
    '/accounts/login/': 200,
}

for route, expected_status in public_routes.items():
    response = client.get(route, secure=True)
    print(route, response.status_code)
    assert response.status_code == expected_status

client.force_login(user)

authenticated_routes = [
    '/dashboard/',
    '/applications/',
    '/insights/',
]

for route in authenticated_routes:
    response = client.get(route, secure=True)
    print(route, response.status_code)
    assert response.status_code == 200

application = JobApplication.objects.create(
    owner=user,
    title='Sprint 4 Day 4 Smoke Role',
    company='Trackly Verification',
    status=JobApplication.Status.SAVED,
    job_link='https://example.com/day-4-smoke-role',
    job_description='Python Django PostgreSQL Docker production verification.',
    notes='Created by Sprint 4 Day 4 verification runbook.',
)
assert JobApplication.objects.filter(pk=application.pk, owner=user).exists()

application.status = JobApplication.Status.APPLIED
application.notes = 'Updated by Sprint 4 Day 4 verification runbook.'
application.save()
application.refresh_from_db()
assert application.status == JobApplication.Status.APPLIED

application_pk = application.pk
application.delete()
assert not JobApplication.objects.filter(pk=application_pk).exists()

unauthenticated_client = Client(HTTP_HOST='$PRODUCTION_HOST')
api_response = unauthenticated_client.get('/api/v1/jobs/applications/', secure=True)
print('/api/v1/jobs/applications/', api_response.status_code)
assert api_response.status_code in {401, 403}

token_response = Client(HTTP_HOST='$PRODUCTION_HOST').post(
    '/api/v1/auth/token/',
    data={'email': email, 'password': password},
    content_type='application/json',
    secure=True,
)
print('/api/v1/auth/token/', token_response.status_code)
assert token_response.status_code == 200
assert 'access' in token_response.json()

print('PRODUCT_SMOKE_CHECKS_READY')
"

print_section "Verify release-aware logging configuration under production settings"

run production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
import logging
from django.conf import settings

assert isinstance(settings.LOGGING, dict)
assert 'release=%(release_version)s' in settings.LOGGING['formatters']['standard']['format']
logging.getLogger('django').info('TRACKLY_DAY_4_LOGGING_PROBE')
print('LOGGING_CONFIG_READY')
"

print_section "Run focused production-readiness regression tests"

run compose_exec pytest config/tests/test_production_settings.py config/tests/test_health_check.py -q

print_section "Run final Day 4 CI-quality gates"

run compose_exec sh -lc "
python -m ruff check . &&
python -m black . --check &&
python manage.py check --settings=config.settings.test &&
python manage.py makemigrations --check --dry-run --settings=config.settings.test &&
python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml
"

if [[ -n "$TRACKLY_LIVE_URL" ]]; then
  verify_live_url
else
  print_section "Skip live URL verification"

  printf 'TRACKLY_LIVE_URL is not set.\n'
  printf 'Local deployment contract verification completed.\n'

  if [[ "$REQUIRE_LIVE_DEPLOYMENT" == "1" ]]; then
    printf 'REQUIRE_LIVE_DEPLOYMENT=1, so live URL verification is required.\n' >&2
    printf 'Run with TRACKLY_LIVE_URL=https://your-render-url.onrender.com\n' >&2
    exit 1
  fi
fi

print_section "Check Git working tree status"

run git status --short

print_section "Sprint 4 Day 4 verification complete"

printf 'Verified Docker Compose project: %s\n' "$COMPOSE_PROJECT_NAME"
printf 'Verified web service: %s\n' "$WEB_SERVICE"
printf 'Verified web container prefix: %s\n' "$EXPECTED_WEB_CONTAINER_PREFIX"
printf 'Verified PostgreSQL image: %s\n' "$EXPECTED_POSTGRES_IMAGE"
printf 'Verified production settings module: %s\n' "$PRODUCTION_SETTINGS"
printf 'Verified production host: %s\n' "$PRODUCTION_HOST"
printf 'Verified Dockerfile default command: Gunicorn.\n'
printf 'Verified local Docker Compose override: runserver.\n'
printf 'Verified Render deployment file: render.yaml.\n'
printf 'Verified production deploy check, migrations, seeded roles, static collection, health endpoint, product route smoke checks, API auth, and Gunicorn config.\n'

if [[ -n "$TRACKLY_LIVE_URL" ]]; then
  printf 'Verified live Render URL: %s\n' "$(normalise_live_url "$TRACKLY_LIVE_URL")"
else
  printf 'Live Render URL verification skipped because TRACKLY_LIVE_URL was not set.\n'
fi

printf 'Sprint 4 Day 4 Render deployment and release verification baseline passed.\n'
