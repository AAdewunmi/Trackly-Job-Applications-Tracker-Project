#!/usr/bin/env bash
set -Eeuo pipefail

# Sprint 2 Day 1 console-only verification runbook for Trackly.
#
# Purpose:
#   Verify the Sprint 2 Day 1 job application domain model baseline using
#   Docker Compose, the configured web service, PostgreSQL, migrations, and
#   database-backed model tests.
#
# Execution:
#   chmod +x docs/sprint-runbook/sprint-2/sprint-2-day-1.sh
#   ./docs/sprint-runbook/sprint-2/sprint-2-day-1.sh
#
# Expected final receipt:
#   10 passed
#   Sprint 2 Day 1 job application domain baseline verified
#
# Notes:
#   This runbook uses the repository's default Docker Compose project name so
#   container and image names match the rest of the Trackly runbooks. Override
#   the SPRINT2_DAY1_* variables only when you intentionally need custom local
#   values for this verification run.

PROJECT_NAME="${SPRINT2_DAY1_COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
WEB_SERVICE="${SPRINT2_DAY1_WEB_SERVICE:-web}"
DB_SERVICE="${SPRINT2_DAY1_DB_SERVICE:-db}"
DJANGO_SETTINGS_MODULE="${SPRINT2_DAY1_DJANGO_SETTINGS_MODULE:-config.settings.local}"
EXPECTED_POSTGRES_IMAGE="${SPRINT2_DAY1_POSTGRES_IMAGE:-postgres:16-alpine}"

export DJANGO_SECRET_KEY="${SPRINT2_DAY1_DJANGO_SECRET_KEY:-sprint-2-day-1-local-secret-key}"
export DJANGO_DEBUG="${SPRINT2_DAY1_DJANGO_DEBUG:-True}"
export DJANGO_ALLOWED_HOSTS="${SPRINT2_DAY1_DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,0.0.0.0}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${SPRINT2_DAY1_DJANGO_CSRF_TRUSTED_ORIGINS:-http://localhost:8000,http://127.0.0.1:8000}"
export POSTGRES_DB="${SPRINT2_DAY1_POSTGRES_DB:-trackly}"
export POSTGRES_USER="${SPRINT2_DAY1_POSTGRES_USER:-trackly_user}"
export POSTGRES_PASSWORD="${SPRINT2_DAY1_POSTGRES_PASSWORD:-trackly_password}"
export POSTGRES_HOST="${SPRINT2_DAY1_POSTGRES_HOST:-db}"
export POSTGRES_PORT="${SPRINT2_DAY1_POSTGRES_PORT:-5432}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

COMPOSE=(
  docker compose
  -p "${PROJECT_NAME}"
)

print_step() {
  echo
  echo "==> $1"
}

run() {
  echo
  echo "$ $*"
  "$@"
}

require_file() {
  local file_path="$1"

  if [[ ! -f "${file_path}" ]]; then
    echo "Missing required file: ${file_path}" >&2
    exit 1
  fi
}

require_directory() {
  local directory_path="$1"

  if [[ ! -d "${directory_path}" ]]; then
    echo "Missing required directory: ${directory_path}" >&2
    exit 1
  fi
}

print_step "Confirm repository root"
run cd "${REPOSITORY_ROOT}"
pwd

print_step "Confirm required Sprint 2 Day 1 files exist"
require_file manage.py
require_file docker-compose.yml
require_file config/settings/base.py
require_file config/settings/local.py
require_file config/settings/test.py
require_directory apps
require_directory apps/jobs
require_file apps/jobs/__init__.py
require_file apps/jobs/apps.py
require_file apps/jobs/models.py
require_file apps/jobs/admin.py
require_file apps/jobs/factories.py
require_file apps/jobs/migrations/0001_initial.py
require_file apps/jobs/tests/__init__.py
require_file apps/jobs/tests/test_models.py
require_file docs/domain-model.md
require_file pytest.ini

print_step "Confirm Docker Compose project and service expectations"
echo "Docker Compose project name: ${PROJECT_NAME}"
echo "Web service: ${WEB_SERVICE}"
echo "Database service: ${DB_SERVICE}"
echo "Expected PostgreSQL image: ${EXPECTED_POSTGRES_IMAGE}"

run "${COMPOSE[@]}" config --services

if ! "${COMPOSE[@]}" config --services | grep -qx "${WEB_SERVICE}"; then
  echo "Expected Docker Compose service not found: ${WEB_SERVICE}" >&2
  exit 1
fi

if ! "${COMPOSE[@]}" config --services | grep -qx "${DB_SERVICE}"; then
  echo "Expected Docker Compose service not found: ${DB_SERVICE}" >&2
  exit 1
fi

print_step "Start PostgreSQL and web services"
run "${COMPOSE[@]}" up -d "${DB_SERVICE}" "${WEB_SERVICE}"

print_step "Confirm containers are running"
run "${COMPOSE[@]}" ps

print_step "Confirm PostgreSQL image"
DB_CONTAINER_ID="$("${COMPOSE[@]}" ps -q "${DB_SERVICE}")"
DB_IMAGE_ACTUAL="$(docker inspect -f '{{.Config.Image}}' "${DB_CONTAINER_ID}")"
echo "DB_IMAGE=${DB_IMAGE_ACTUAL}"

if [[ "${DB_IMAGE_ACTUAL}" != "${EXPECTED_POSTGRES_IMAGE}" ]]; then
  echo "Expected DB image ${EXPECTED_POSTGRES_IMAGE}, got ${DB_IMAGE_ACTUAL}" >&2
  exit 1
fi

print_step "Wait for PostgreSQL to become ready"
for attempt in {1..20}; do
  if "${COMPOSE[@]}" exec -T "${DB_SERVICE}" pg_isready \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    echo "PostgreSQL is ready after ${attempt} attempt(s)."
    break
  fi

  if [[ "${attempt}" -eq 20 ]]; then
    echo "PostgreSQL did not become ready in time." >&2
    exit 1
  fi

  sleep 1
done

print_step "Verify Django can load local settings"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py check "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Verify jobs migrations are up to date"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Apply database migrations"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py migrate --noinput "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Verify jobs app migrations are registered"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py showmigrations jobs "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Run Sprint 2 Day 1 model tests"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  pytest apps/jobs/tests/test_models.py -q

print_step "Sprint 2 Day 1 verification complete"

cat <<'EOF'
Expected receipt:
10 passed

Verified:
- Docker Compose uses the Trackly project name.
- The web service is executed through Docker Compose.
- PostgreSQL image expectation is postgres:16-alpine.
- PostgreSQL is ready before Django commands run.
- Django local settings load successfully.
- jobs migrations are present and up to date.
- database migrations apply non-interactively.
- JobApplication and ApplicationNote model tests pass.

Sprint 2 Day 1 job application domain baseline verified
EOF
