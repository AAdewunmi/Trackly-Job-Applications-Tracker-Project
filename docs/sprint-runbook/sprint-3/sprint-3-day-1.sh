#!/usr/bin/env bash
#
# Sprint 3 Day 1 console-only verification runbook for Trackly.
#
# Scope:
# Verify DRF setup, JWT authentication, /api/v1/ routing, secured job
# application API endpoints, and ownership-aware API tests.
#
# Expected Docker resources:
# - Compose project: trackly-job-applications-tracker-project
# - Web container prefix: trackly-job-applications-tracker-project-web
# - Database image: postgres:16-alpine
#
# Execution instructions:
# Run from the repository root, or from any directory:
#
#   chmod +x docs/sprint-runbook/sprint-3/sprint-3-day-1.sh
#   ./docs/sprint-runbook/sprint-3/sprint-3-day-1.sh
#
# The script starts the web and database services if needed.

set -Eeuo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
EXPECTED_WEB_CONTAINER_PREFIX="${EXPECTED_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.local}"
EXPECTED_POSTGRES_IMAGE="${EXPECTED_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_USER="${POSTGRES_USER:-trackly_user}"
POSTGRES_DB="${POSTGRES_DB:-trackly}"
API_SMOKE_EMAIL="${API_SMOKE_EMAIL:-api.smoke@example.com}"
API_SMOKE_PASSWORD="${API_SMOKE_PASSWORD:-SmokePass12345}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"


compose() {
  docker compose -p "${COMPOSE_PROJECT_NAME}" "$@"
}


print_header() {
  printf "\n==> %s\n\n" "$1"
}


print_command() {
  printf "$ %s\n" "$*"
}


run_command() {
  print_command "$@"
  "$@"
}


run_secret_command() {
  printf "$ %s\n" "$1"
  shift
  "$@"
}


assert_file_exists() {
  local file_path="$1"

  if [[ ! -f "${file_path}" ]]; then
    printf "Missing required file: %s\n" "${file_path}" >&2
    exit 1
  fi
}


assert_directory_exists() {
  local directory_path="$1"

  if [[ ! -d "${directory_path}" ]]; then
    printf "Missing required directory: %s\n" "${directory_path}" >&2
    exit 1
  fi
}


wait_for_postgres() {
  local attempt
  local max_attempts=30

  for attempt in $(seq 1 "${max_attempts}"); do
    if compose exec -T "${DB_SERVICE}" pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
      printf "PostgreSQL is ready after %s attempt(s).\n" "${attempt}"
      return 0
    fi

    printf "PostgreSQL is not ready yet. Attempt %s/%s...\n" "${attempt}" "${max_attempts}"
    sleep 1
  done

  printf "PostgreSQL did not become ready after %s attempts.\n" "${max_attempts}" >&2
  return 1
}


print_header "Confirm repository root"

run_command cd "${REPOSITORY_ROOT}"
pwd

print_header "Confirm Sprint 3 Day 1 files exist"

assert_file_exists "manage.py"
assert_file_exists "docker-compose.yml"
assert_file_exists "requirements.txt"
assert_file_exists "config/settings/base.py"
assert_file_exists "config/settings/local.py"
assert_file_exists "config/urls.py"
assert_file_exists "docs/api-contract.md"

assert_directory_exists "apps/jobs/api"
assert_file_exists "apps/jobs/api/__init__.py"
assert_file_exists "apps/jobs/api/serializers.py"
assert_file_exists "apps/jobs/api/views.py"
assert_file_exists "apps/jobs/api/urls.py"

assert_directory_exists "apps/jobs/tests/api"
assert_file_exists "apps/jobs/tests/api/__init__.py"
assert_file_exists "apps/jobs/tests/api/test_job_application_api.py"
assert_file_exists "apps/jobs/tests/api/test_api_permissions.py"

print_header "Confirm Docker Compose project and service expectations"

printf "Docker Compose project name: %s\n" "${COMPOSE_PROJECT_NAME}"
printf "Expected web container prefix: %s\n" "${EXPECTED_WEB_CONTAINER_PREFIX}"
printf "Web service: %s\n" "${WEB_SERVICE}"
printf "Database service: %s\n" "${DB_SERVICE}"
printf "Expected PostgreSQL image: %s\n" "${EXPECTED_POSTGRES_IMAGE}"

run_command compose config --services

if ! compose config --services | grep -qx "${WEB_SERVICE}"; then
  printf "Expected Docker Compose service not found: %s\n" "${WEB_SERVICE}" >&2
  exit 1
fi

if ! compose config --services | grep -qx "${DB_SERVICE}"; then
  printf "Expected Docker Compose service not found: %s\n" "${DB_SERVICE}" >&2
  exit 1
fi

print_header "Build and start Docker services"

run_command compose build "${WEB_SERVICE}"
run_command compose up -d "${DB_SERVICE}" "${WEB_SERVICE}"

print_header "Confirm services are running"

run_command compose ps

print_header "Confirm web container uses the expected Compose project prefix"

WEB_CONTAINER_NAME="$(
  compose ps "${WEB_SERVICE}" --format json |
  python3 -c 'import json, sys; print(json.load(sys.stdin)["Name"])'
)"
printf "WEB_CONTAINER_NAME=%s\n" "${WEB_CONTAINER_NAME}"

if [[ "${WEB_CONTAINER_NAME}" != "${EXPECTED_WEB_CONTAINER_PREFIX}"* ]]; then
  printf "Expected web container name to start with %s but found %s\n" "${EXPECTED_WEB_CONTAINER_PREFIX}" "${WEB_CONTAINER_NAME}" >&2
  exit 1
fi

print_header "Confirm PostgreSQL image"

DB_IMAGE="$(
  compose ps "${DB_SERVICE}" --format json |
  python3 -c 'import json, sys; print(json.load(sys.stdin)["Image"])'
)"
printf "DB_IMAGE=%s\n" "${DB_IMAGE}"

if [[ "${DB_IMAGE}" != "${EXPECTED_POSTGRES_IMAGE}" ]]; then
  printf "Expected database image %s but found %s\n" "${EXPECTED_POSTGRES_IMAGE}" "${DB_IMAGE}" >&2
  exit 1
fi

print_header "Wait for PostgreSQL readiness"

wait_for_postgres

print_header "Verify Django system check"

run_command compose exec -T "${WEB_SERVICE}" python manage.py check "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Verify migrations are up to date"

run_command compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Apply migrations"

run_command compose exec -T "${WEB_SERVICE}" python manage.py migrate --noinput "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Verify DRF, SimpleJWT, and API modules import"

run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
import rest_framework
import rest_framework_simplejwt

from apps.jobs.api.serializers import JobApplicationSerializer
from apps.jobs.api.views import JobApplicationDetailAPIView
from apps.jobs.api.views import JobApplicationListCreateAPIView

print(rest_framework.__name__)
print(rest_framework_simplejwt.__name__)
print(JobApplicationSerializer.__name__)
print(JobApplicationListCreateAPIView.__name__)
print(JobApplicationDetailAPIView.__name__)
"

print_header "Verify corrected Sprint 3 Day 1 URL names and paths"

run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from django.urls import reverse

expected_urls = {
    'token_obtain_pair': '/api/v1/auth/token/',
    'token_refresh': '/api/v1/auth/token/refresh/',
    'job-application-list-create': '/api/v1/jobs/applications/',
}

for name, expected_url in expected_urls.items():
    actual_url = reverse(name)
    print(f'{name} -> {actual_url}')
    if actual_url != expected_url:
        raise SystemExit(f'Expected {name} to resolve to {expected_url}, got {actual_url}')

detail_url = reverse('job-application-detail', kwargs={'pk': 123})
print(f'job-application-detail -> {detail_url}')
if detail_url != '/api/v1/jobs/applications/123/':
    raise SystemExit(f'Expected job-application-detail to resolve to /api/v1/jobs/applications/123/, got {detail_url}')
"

print_header "Verify Sprint 3 Day 1 API tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/jobs/tests/api -q

print_header "Verify focused style checks for API code and tests"

run_command compose exec -T "${WEB_SERVICE}" python -m ruff check apps/jobs/api apps/jobs/tests/api
run_command compose exec -T "${WEB_SERVICE}" python -m black apps/jobs/api apps/jobs/tests/api --check

print_header "Create console smoke-test user"

run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from django.contrib.auth import get_user_model

User = get_user_model()
User.objects.filter(email='${API_SMOKE_EMAIL}').delete()
User.objects.create_user(
    email='${API_SMOKE_EMAIL}',
    password='${API_SMOKE_PASSWORD}',
    first_name='API',
    last_name='Smoke',
)
print('created')
"

print_header "Obtain JWT access token"

ACCESS_TOKEN="$(
  curl -s -X POST "http://localhost:8000/api/v1/auth/token/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${API_SMOKE_EMAIL}\",\"password\":\"${API_SMOKE_PASSWORD}\"}" |
  python3 -c "import json, sys; print(json.load(sys.stdin)['access'])"
)"
printf "Access token obtained.\n"

print_header "Confirm unauthenticated API access is rejected"

UNAUTH_STATUS="$(
  curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/jobs/applications/"
)"
printf "GET /api/v1/jobs/applications/ without auth -> %s\n" "${UNAUTH_STATUS}"

if [[ "${UNAUTH_STATUS}" != "401" ]]; then
  printf "Expected unauthenticated /api/v1/jobs/applications/ request to return 401, got %s\n" "${UNAUTH_STATUS}" >&2
  exit 1
fi

print_header "Create a job application through the API"

CREATE_RESPONSE="$(
  curl -s -X POST "http://localhost:8000/api/v1/jobs/applications/" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"title":"Graduate Django Engineer","company":"Trackly Labs","status":"applied","job_link":"https://example.com/jobs/1","applied_date":"2026-04-01","job_description":"Python Django REST API PostgreSQL Docker testing.","notes":"Applied through careers page."}'
)"
printf "%s\n" "${CREATE_RESPONSE}"

APPLICATION_ID="$(
  printf "%s" "${CREATE_RESPONSE}" |
  python3 -c "import json, sys; data=json.load(sys.stdin); print(data['id']); assert data['title'] == 'Graduate Django Engineer'"
)"
printf "APPLICATION_ID=%s\n" "${APPLICATION_ID}"

print_header "Retrieve, update, list, and delete the API-created application"

run_secret_command \
  "curl -s http://localhost:8000/api/v1/jobs/applications/${APPLICATION_ID}/ -H 'Authorization: Bearer <access-token>'" \
  curl -s "http://localhost:8000/api/v1/jobs/applications/${APPLICATION_ID}/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
printf "\n"

UPDATE_STATUS="$(
  curl -s -o /dev/null -w "%{http_code}" -X PATCH "http://localhost:8000/api/v1/jobs/applications/${APPLICATION_ID}/" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"status":"interviewing"}'
)"
printf "PATCH /api/v1/jobs/applications/%s/ -> %s\n" "${APPLICATION_ID}" "${UPDATE_STATUS}"

if [[ "${UPDATE_STATUS}" != "200" ]]; then
  printf "Expected update to return 200, got %s\n" "${UPDATE_STATUS}" >&2
  exit 1
fi

run_secret_command \
  "curl -s http://localhost:8000/api/v1/jobs/applications/ -H 'Authorization: Bearer <access-token>'" \
  curl -s "http://localhost:8000/api/v1/jobs/applications/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
printf "\n"

DELETE_STATUS="$(
  curl -s -o /dev/null -w "%{http_code}" -X DELETE "http://localhost:8000/api/v1/jobs/applications/${APPLICATION_ID}/" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}"
)"
printf "DELETE /api/v1/jobs/applications/%s/ -> %s\n" "${APPLICATION_ID}" "${DELETE_STATUS}"

if [[ "${DELETE_STATUS}" != "204" ]]; then
  printf "Expected delete to return 204, got %s\n" "${DELETE_STATUS}" >&2
  exit 1
fi

print_header "Sprint 3 Day 1 verification complete"

printf "Verified DRF/JWT setup, corrected /api/v1/jobs/applications/ routes, authenticated API access, ownership tests, Docker web container prefix, and postgres:16-alpine.\n"
