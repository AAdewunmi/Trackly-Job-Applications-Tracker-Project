#!/usr/bin/env bash
#
# Sprint 4 Day 5 console-only verification runbook for Trackly.
#
# Purpose:
# Verify the completed SaaS MVP release baseline against the current repository:
# - Docker Compose starts the expected web and PostgreSQL services
# - PostgreSQL uses postgres:16-alpine
# - README and reviewer documentation match the final MVP shape
# - API, AI/NLP, architecture, deployment, demo, and final verification docs exist
# - Ruff, Black, Django checks, migration drift checks, pytest, coverage,
#   production deploy checks, production static collection, and Render blueprint
#   contract tests pass
# - local health and API auth contracts are smoke-checked
# - optional live Render URL checks can run when a deployment exists
# - optional release tag creation remains explicit and opt-in
#
# Execution:
# chmod +x docs/sprint-runbook/sprint-4/sprint-4-day-5.sh
# ./docs/sprint-runbook/sprint-4/sprint-4-day-5.sh
#
# Expected Docker Compose project:
# trackly-job-applications-tracker-project
#
# Expected web service:
# web
#
# Expected web container name prefix:
# trackly-job-applications-tracker-project-web
#
# Expected PostgreSQL image:
# postgres:16-alpine
#
# Optional live verification after Render deployment:
# TRACKLY_LIVE_URL=https://your-render-url.onrender.com ./docs/sprint-runbook/sprint-4/sprint-4-day-5.sh
#
# Strict live verification:
# REQUIRE_LIVE_DEPLOYMENT=1 TRACKLY_LIVE_URL=https://your-render-url.onrender.com ./docs/sprint-runbook/sprint-4/sprint-4-day-5.sh
#
# Optional release tag creation:
# CREATE_RELEASE_TAG=1 ./docs/sprint-runbook/sprint-4/sprint-4-day-5.sh
#
# Optional release tag creation and push:
# CREATE_RELEASE_TAG=1 PUSH_RELEASE_TAG=1 ./docs/sprint-runbook/sprint-4/sprint-4-day-5.sh
#
# Strict release tag verification:
# REQUIRE_RELEASE_TAG=1 ./docs/sprint-runbook/sprint-4/sprint-4-day-5.sh

set -Eeuo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"
EXPECTED_WEB_CONTAINER_PREFIX="${EXPECTED_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
EXPECTED_POSTGRES_IMAGE="${EXPECTED_POSTGRES_IMAGE:-postgres:16-alpine}"

PRODUCTION_SETTINGS="${PRODUCTION_SETTINGS:-config.settings.production}"
PRODUCTION_HOST="${PRODUCTION_HOST:-trackly.example.com}"
PRODUCTION_ORIGIN="${PRODUCTION_ORIGIN:-https://trackly.example.com}"
PRODUCTION_SECRET_KEY="${PRODUCTION_SECRET_KEY:-local-production-secret-key-with-enough-length-for-day-5-checks}"
PRODUCTION_DATABASE_URL="${PRODUCTION_DATABASE_URL:-postgres://trackly_user:trackly_password@db:5432/trackly}"
PRODUCTION_RELEASE_VERSION="${PRODUCTION_RELEASE_VERSION:-v0.1.0-mvp-local}"
POSTGRES_READINESS_USER="${POSTGRES_READINESS_USER:-trackly_user}"
POSTGRES_READINESS_DB="${POSTGRES_READINESS_DB:-trackly}"

TRACKLY_LIVE_URL="${TRACKLY_LIVE_URL:-}"
REQUIRE_LIVE_DEPLOYMENT="${REQUIRE_LIVE_DEPLOYMENT:-0}"

RELEASE_TAG="${RELEASE_TAG:-v0.1.0-mvp}"
CREATE_RELEASE_TAG="${CREATE_RELEASE_TAG:-0}"
PUSH_RELEASE_TAG="${PUSH_RELEASE_TAG:-0}"
REQUIRE_RELEASE_TAG="${REQUIRE_RELEASE_TAG:-0}"

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
  local running_state

  container_id="$(get_container_id "$service_name")"

  if [[ -z "$container_id" ]]; then
    printf 'No container found for service: %s\n' "$service_name" >&2
    exit 1
  fi

  running_state="$(docker inspect --format '{{.State.Running}}' "$container_id")"

  if [[ "$running_state" != "true" ]]; then
    printf 'Container for service %s is not running.\n' "$service_name" >&2
    exit 1
  fi

  printf 'Container for service %s is running: %s\n' "$service_name" "$container_id"
}

assert_web_container_name() {
  local container_id
  local container_name

  container_id="$(get_container_id "$WEB_SERVICE")"
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
  local configured_image

  container_id="$(get_container_id "$DB_SERVICE")"
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
    if compose exec -T "$DB_SERVICE" pg_isready \
      -U "$POSTGRES_READINESS_USER" \
      -d "$POSTGRES_READINESS_DB" >/dev/null 2>&1; then
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
  local status_code

  live_url="$(normalise_live_url "$TRACKLY_LIVE_URL")"

  print_section "Verify optional live Render URL"

  printf 'Live URL selected: %s\n' "$live_url"

  run curl --fail --silent --show-error --location "$live_url/health/"
  run curl --fail --silent --show-error --location "$live_url/accounts/signup/" --output /tmp/trackly_day_5_signup.html
  run test -s /tmp/trackly_day_5_signup.html
  run curl --fail --silent --show-error --location "$live_url/accounts/login/" --output /tmp/trackly_day_5_login.html
  run test -s /tmp/trackly_day_5_login.html

  print_section "Verify optional live secured API rejection"

  status_code="$(
    curl --silent \
      --output /tmp/trackly_day_5_api_response.json \
      --write-out '%{http_code}' \
      "$live_url/api/v1/jobs/applications/"
  )"

  printf 'Unauthenticated applications API status: %s\n' "$status_code"

  if [[ "$status_code" != "401" && "$status_code" != "403" ]]; then
    printf 'Expected unauthenticated API request to return 401 or 403.\n' >&2
    printf 'Actual status: %s\n' "$status_code" >&2
    printf 'Response body:\n' >&2
    cat /tmp/trackly_day_5_api_response.json >&2
    exit 1
  fi

  printf 'Live API unauthenticated rejection verified.\n'
}

verify_or_create_release_tag() {
  print_section "Verify optional MVP release tag"

  if git rev-parse "$RELEASE_TAG" >/dev/null 2>&1; then
    printf 'Release tag already exists: %s\n' "$RELEASE_TAG"
    return 0
  fi

  if [[ "$CREATE_RELEASE_TAG" == "1" ]]; then
    run git tag "$RELEASE_TAG"

    if [[ "$PUSH_RELEASE_TAG" == "1" ]]; then
      run git push origin "$RELEASE_TAG"
    else
      printf 'Release tag created locally but not pushed. Set PUSH_RELEASE_TAG=1 to push it.\n'
    fi

    return 0
  fi

  printf 'Release tag does not exist yet: %s\n' "$RELEASE_TAG"

  if [[ "$REQUIRE_RELEASE_TAG" == "1" ]]; then
    printf 'REQUIRE_RELEASE_TAG=1, so the release tag is required.\n' >&2
    printf 'Run with CREATE_RELEASE_TAG=1 to create the local tag.\n' >&2
    exit 1
  fi

  printf 'Release tag creation skipped because CREATE_RELEASE_TAG=1 was not set.\n'
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
require_file ".github/workflows/ci.yml"
require_file "README.md"
require_file "RUNBOOK.md"
require_file "render.yaml"

require_file "docs/architecture.md"
require_file "docs/api-contract.md"
require_file "docs/ai-nlp-contract.md"
require_file "docs/ci.md"
require_file "docs/deployment.md"
require_file "docs/demo-script.md"
require_file "docs/final-verification.md"
require_file "docs/local-setup.md"

printf 'Repository root verified: %s\n' "$(pwd)"

print_section "Verify required local commands"

require_command "docker"
require_command "git"
require_command "curl"

run docker --version
run docker compose version
run git --version
run curl --version

print_section "Verify documentation package"

require_text "README.md" "MVP Scope" "README MVP scope"
require_text "README.md" "How To Use The Repo" "README repository usage"
require_text "README.md" "How To Use Trackly" "README product usage"
require_text "README.md" "Documentation Coverage" "README documentation coverage"
require_text "README.md" "Potential Extensions" "README limitations and growth path"
require_text "README.md" "Repository Structure" "README repository structure"
require_text "README.md" "/api/v1/" "README API surface"
require_text "README.md" "Render blueprint" "README deployment baseline"
require_text "README.md" "production static-file collection" "README CI static collection"

require_text "docs/architecture.md" "Architecture Principles" "architecture principles"
require_text "docs/architecture.md" "Request Surfaces" "architecture request surfaces"
require_text "docs/architecture.md" "Data Ownership Model" "architecture ownership model"
require_text "docs/architecture.md" "collectstatic --noinput" "architecture CI static collection"

require_text "docs/api-contract.md" "/api/v1/jobs/applications/" "job application API path"
require_text "docs/api-contract.md" "/api/v1/insights/generate/" "insight generation API path"
require_text "docs/api-contract.md" "Authorization: Bearer" "JWT bearer auth"
require_text "docs/api-contract.md" "ownership boundaries" "API ownership boundary"

require_text "docs/ai-nlp-contract.md" "Non-goals" "AI/NLP non-goals"
require_text "docs/ai-nlp-contract.md" "nltk-tfidf-cosine-v1" "AI/NLP pipeline version"
require_text "docs/ai-nlp-contract.md" "Score Labels" "AI/NLP score labels"
require_text "docs/ai-nlp-contract.md" "source_hash" "AI/NLP source hash"

require_text "docs/deployment.md" "Render" "deployment Render target"
require_text "docs/deployment.md" "DATABASE_URL" "deployment database URL"
require_text "docs/deployment.md" "/health/" "deployment health check"
require_text "docs/deployment.md" "collectstatic" "deployment static collection"

require_text "docs/demo-script.md" "Trackly Demo Script" "demo script title"
require_text "docs/demo-script.md" "/dashboard/" "demo dashboard route"
require_text "docs/demo-script.md" "/applications/" "demo applications route"
require_text "docs/demo-script.md" "/insights/" "demo insights route"

require_text "docs/final-verification.md" "Trackly Final Verification Checklist" "final verification title"
require_text "docs/final-verification.md" "collectstatic --noinput" "final verification static collection"
require_text "docs/final-verification.md" "/api/v1/jobs/applications/" "final verification API path"
require_text "docs/final-verification.md" "v0.1.0-mvp" "final verification release tag"

print_section "Verify runtime and deployment files"

require_text "docker-compose.yml" "web:" "Compose web service"
require_text "docker-compose.yml" "db:" "Compose database service"
require_text "docker-compose.yml" "postgres:16-alpine" "Compose PostgreSQL image"
require_text "docker-compose.yml" "config.settings.local" "Compose local settings"

require_text "Dockerfile" "FROM python:3.12-slim" "Docker Python runtime"
require_text "Dockerfile" "gunicorn" "Docker Gunicorn command"
require_text "Dockerfile" "nltk.downloader" "Docker NLTK data provisioning"

require_text "render.yaml" "name: trackly-web" "Render web service"
require_text "render.yaml" "runtime: docker" "Render Docker runtime"
require_text "render.yaml" "python manage.py migrate --noinput" "Render migration startup"
require_text "render.yaml" "python manage.py collectstatic --noinput" "Render static startup"
require_text "render.yaml" "gunicorn config.wsgi:application" "Render Gunicorn startup"
require_text "render.yaml" "healthCheckPath: /health/" "Render health path"
require_text "render.yaml" "name: trackly-db" "Render database"
require_text "render.yaml" "DATABASE_URL" "Render database URL"

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

print_section "Verify commands inside web container"

compose_exec sh -lc "command -v python"
compose_exec sh -lc "command -v pytest"
compose_exec sh -lc "command -v gunicorn"

print_section "Seed deterministic local demo data"

compose_exec python manage.py seed_demo_data

print_section "Run Ruff quality gate"

compose_exec python -m ruff check .

print_section "Run Black formatting gate"

compose_exec python -m black . --check

print_section "Run Django startup check"

compose_exec python manage.py check --settings=config.settings.test

print_section "Verify no migration drift"

compose_exec python manage.py makemigrations --check --dry-run --settings=config.settings.test

print_section "Apply migrations through test settings"

compose_exec python manage.py migrate --noinput --settings=config.settings.test

print_section "Run full test suite with coverage"

compose_exec python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml

print_section "Run focused release-readiness regression tests"

compose_exec pytest \
  config/tests/test_production_settings.py \
  config/tests/test_health_check.py \
  config/tests/test_render_blueprint.py \
  -q

print_section "Run production deploy check"

production_exec python manage.py check --deploy --settings="$PRODUCTION_SETTINGS"

print_section "Collect static files with production settings"

production_exec python manage.py collectstatic --noinput --settings="$PRODUCTION_SETTINGS"

print_section "Verify collected static assets"

compose_exec sh -lc "test -d staticfiles && find staticfiles -type f | head -n 10"

print_section "Verify production health endpoint"

production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
from django.test import Client

response = Client().get('/health/', secure=True, HTTP_HOST='$PRODUCTION_HOST')
body = response.content.decode()

print(response.status_code)
print(body)

assert response.status_code == 200
assert 'ok' in body.lower()
assert '$PRODUCTION_RELEASE_VERSION' in body
"

print_section "Verify local product and API smoke path"

compose_exec python manage.py shell -c "
from django.contrib.auth import get_user_model
from django.test import Client

from apps.jobs.models import JobApplication

User = get_user_model()

email = 'sprint4-day5-smoke@trackly.local'
password = 'TracklySmokePass123'

user, _created = User.objects.update_or_create(
    email=email,
    defaults={
        'first_name': 'Release',
        'last_name': 'Smoke',
        'is_active': True,
    },
)
user.set_password(password)
user.save()

client = Client(HTTP_HOST='localhost')

for route in ['/', '/accounts/signup/', '/accounts/login/', '/health/']:
    response = client.get(route)
    print(route, response.status_code)
    assert response.status_code == 200

client.force_login(user)

for route in ['/dashboard/', '/applications/', '/insights/']:
    response = client.get(route)
    print(route, response.status_code)
    assert response.status_code == 200

application = JobApplication.objects.create(
    owner=user,
    title='Day 5 Release Smoke Role',
    company='Trackly Release Verification',
    status=JobApplication.Status.SAVED,
    job_link='https://example.com/day-5-release-smoke-role',
    job_description='Python Django PostgreSQL Docker CI release verification.',
    notes='Created by Day 5 verification runbook.',
)

assert JobApplication.objects.filter(pk=application.pk, owner=user).exists()

application.status = JobApplication.Status.APPLIED
application.notes = 'Updated by Day 5 verification runbook.'
application.save()
application.refresh_from_db()

assert application.status == JobApplication.Status.APPLIED

application_pk = application.pk
application.delete()

assert not JobApplication.objects.filter(pk=application_pk).exists()

unauthenticated_client = Client(HTTP_HOST='localhost')
api_response = unauthenticated_client.get('/api/v1/jobs/applications/')

print('/api/v1/jobs/applications/', api_response.status_code)

assert api_response.status_code in {401, 403}

token_response = Client(HTTP_HOST='localhost').post(
    '/api/v1/auth/token/',
    data={'email': email, 'password': password},
    content_type='application/json',
)

print('/api/v1/auth/token/', token_response.status_code)

assert token_response.status_code == 200
assert 'access' in token_response.json()

print('LOCAL_PRODUCT_SMOKE_CHECKS_READY')
"

print_section "Verify release-aware logging config"

production_exec python manage.py shell --settings="$PRODUCTION_SETTINGS" -c "
import logging
from django.conf import settings

assert isinstance(settings.LOGGING, dict)
assert 'release=%(release_version)s' in settings.LOGGING['formatters']['standard']['format']

logging.getLogger('django').info('TRACKLY_DAY_5_RELEASE_LOGGING_PROBE')

print('RELEASE_LOGGING_READY')
"

print_section "Verify Gunicorn production config"

production_exec sh -lc "gunicorn config.wsgi:application --check-config"

if [[ -n "$TRACKLY_LIVE_URL" ]]; then
  verify_live_url
else
  print_section "Skip optional live URL verification"

  printf 'TRACKLY_LIVE_URL is not set.\n'
  printf 'Local final release verification completed.\n'

  if [[ "$REQUIRE_LIVE_DEPLOYMENT" == "1" ]]; then
    printf 'REQUIRE_LIVE_DEPLOYMENT=1, so live URL verification is required.\n' >&2
    printf 'Run with TRACKLY_LIVE_URL=https://your-render-url.onrender.com\n' >&2
    exit 1
  fi
fi

verify_or_create_release_tag

print_section "Check Git working tree status"

run git status --short

print_section "Sprint 4 Day 5 verification complete"

printf 'Verified Docker Compose project: %s\n' "$COMPOSE_PROJECT_NAME"
printf 'Verified web service: %s\n' "$WEB_SERVICE"
printf 'Verified web container prefix: %s\n' "$EXPECTED_WEB_CONTAINER_PREFIX"
printf 'Verified PostgreSQL image: %s\n' "$EXPECTED_POSTGRES_IMAGE"
printf 'Verified production settings module: %s\n' "$PRODUCTION_SETTINGS"
printf 'Verified release version: %s\n' "$PRODUCTION_RELEASE_VERSION"
printf 'Verified documentation package: README, architecture, API contract, AI/NLP contract, deployment guide, demo script, final verification checklist.\n'
printf 'Verified release gates: Ruff, Black, Django check, migration drift check, pytest coverage, production deploy check, static collection, health endpoint, product smoke path, API auth, logging, Gunicorn config.\n'

if [[ -n "$TRACKLY_LIVE_URL" ]]; then
  printf 'Verified live Render URL: %s\n' "$(normalise_live_url "$TRACKLY_LIVE_URL")"
else
  printf 'Live Render URL verification skipped because TRACKLY_LIVE_URL was not set.\n'
fi

if git rev-parse "$RELEASE_TAG" >/dev/null 2>&1; then
  printf 'Verified MVP release tag: %s\n' "$RELEASE_TAG"
else
  printf 'MVP release tag not created by this run because CREATE_RELEASE_TAG=1 was not set: %s\n' "$RELEASE_TAG"
fi

printf 'Sprint 4 Day 5 final documentation, demo narrative, and MVP release baseline passed.\n'
