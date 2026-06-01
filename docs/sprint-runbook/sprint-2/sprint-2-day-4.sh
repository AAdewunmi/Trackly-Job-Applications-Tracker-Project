#!/usr/bin/env bash
set -Eeuo pipefail

# Sprint 2 Day 4 console-only verification runbook for Trackly.
#
# Purpose:
#   Verify the application note model, inline note-entry workflow, application
#   ownership enforcement, Docker Compose services, PostgreSQL image, Django
#   migrations, and jobs app regression coverage.
#
# Execution:
#   chmod +x docs/sprint-runbook/sprint-2/sprint-2-day-4.sh
#   ./docs/sprint-runbook/sprint-2/sprint-2-day-4.sh
#
# Expected final receipt:
#   Application note workflow tests pass.
#   Full apps/jobs regression tests pass.
#
# Notes:
#   Docker Compose service names come from docker-compose.yml:
#     - web
#     - db
#
#   The Compose project name is trackly-job-applications-tracker-project,
#   which produces a web container name beginning with:
#     trackly-job-applications-tracker-project-web
#
#   PostgreSQL must use postgres:16-alpine. The PostgreSQL defaults match
#   docker-compose.yml:
#     - database: trackly
#     - user: trackly_user
#
#   Ownership tests were consolidated into the current focused jobs modules:
#     - apps/jobs/tests/test_job_views.py
#     - apps/jobs/tests/test_notes.py

PROJECT_NAME="${SPRINT2_DAY4_COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
WEB_SERVICE="${SPRINT2_DAY4_WEB_SERVICE:-web}"
DB_SERVICE="${SPRINT2_DAY4_DB_SERVICE:-db}"
DJANGO_SETTINGS_MODULE="${SPRINT2_DAY4_DJANGO_SETTINGS_MODULE:-config.settings.local}"
EXPECTED_WEB_CONTAINER_PREFIX="${SPRINT2_DAY4_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
EXPECTED_POSTGRES_IMAGE="${SPRINT2_DAY4_POSTGRES_IMAGE:-postgres:16-alpine}"

export DJANGO_SECRET_KEY="${SPRINT2_DAY4_DJANGO_SECRET_KEY:-sprint-2-day-4-local-secret-key}"
export DJANGO_DEBUG="${SPRINT2_DAY4_DJANGO_DEBUG:-True}"
export DJANGO_ALLOWED_HOSTS="${SPRINT2_DAY4_DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,0.0.0.0}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${SPRINT2_DAY4_DJANGO_CSRF_TRUSTED_ORIGINS:-http://localhost:8000,http://127.0.0.1:8000}"
export POSTGRES_DB="${SPRINT2_DAY4_POSTGRES_DB:-trackly}"
export POSTGRES_USER="${SPRINT2_DAY4_POSTGRES_USER:-trackly_user}"
export POSTGRES_PASSWORD="${SPRINT2_DAY4_POSTGRES_PASSWORD:-trackly_password}"
export POSTGRES_HOST="${SPRINT2_DAY4_POSTGRES_HOST:-db}"
export POSTGRES_PORT="${SPRINT2_DAY4_POSTGRES_PORT:-5432}"

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

wait_for_postgres() {
  local attempt
  local max_attempts=30

  for attempt in $(seq 1 "${max_attempts}"); do
    if "${COMPOSE[@]}" exec -T "${DB_SERVICE}" pg_isready \
      -U "${POSTGRES_USER}" \
      -d "${POSTGRES_DB}" >/dev/null 2>&1; then
      echo "PostgreSQL is ready after ${attempt} attempt(s)."
      return 0
    fi

    echo "PostgreSQL is not ready yet. Attempt ${attempt}/${max_attempts}..."
    sleep 1
  done

  echo "PostgreSQL did not become ready after ${max_attempts} attempts." >&2
  return 1
}

print_step "Confirm repository root"
run cd "${REPOSITORY_ROOT}"
pwd

print_step "Confirm required Sprint 2 Day 4 files exist"
require_file manage.py
require_file docker-compose.yml
require_file pytest.ini
require_file config/urls.py
require_file config/settings/base.py
require_file config/settings/local.py
require_file config/settings/test.py

require_directory apps
require_directory apps/jobs
require_file apps/jobs/__init__.py
require_file apps/jobs/apps.py
require_file apps/jobs/models.py
require_file apps/jobs/admin.py
require_file apps/jobs/forms.py
require_file apps/jobs/selectors.py
require_file apps/jobs/views.py
require_file apps/jobs/urls.py
require_file apps/jobs/factories.py
require_file apps/jobs/tests/__init__.py
require_file apps/jobs/tests/test_models.py
require_file apps/jobs/tests/test_selectors.py
require_file apps/jobs/tests/test_job_views.py
require_file apps/jobs/tests/test_job_update.py
require_file apps/jobs/tests/test_job_delete.py
require_file apps/jobs/tests/test_notes.py

require_directory templates
require_file templates/base.html
require_directory templates/jobs
require_file templates/jobs/application_list.html
require_file templates/jobs/application_form.html
require_file templates/jobs/application_detail.html
require_file templates/jobs/application_confirm_delete.html

print_step "Confirm Docker Compose project and service expectations"
echo "Docker Compose project name: ${PROJECT_NAME}"
echo "Expected web container prefix: ${EXPECTED_WEB_CONTAINER_PREFIX}"
echo "Web service: ${WEB_SERVICE}"
echo "Database service: ${DB_SERVICE}"
echo "Expected PostgreSQL image: ${EXPECTED_POSTGRES_IMAGE}"
echo "PostgreSQL readiness user: ${POSTGRES_USER}"
echo "PostgreSQL readiness database: ${POSTGRES_DB}"

run "${COMPOSE[@]}" config --services

if ! "${COMPOSE[@]}" config --services | grep -qx "${WEB_SERVICE}"; then
  echo "Expected Docker Compose service not found: ${WEB_SERVICE}" >&2
  echo "Available services:" >&2
  "${COMPOSE[@]}" config --services >&2
  exit 1
fi

if ! "${COMPOSE[@]}" config --services | grep -qx "${DB_SERVICE}"; then
  echo "Expected Docker Compose service not found: ${DB_SERVICE}" >&2
  echo "Available services:" >&2
  "${COMPOSE[@]}" config --services >&2
  exit 1
fi

print_step "Start PostgreSQL and web services"
run "${COMPOSE[@]}" up -d "${DB_SERVICE}" "${WEB_SERVICE}"

print_step "Confirm containers are running"
run "${COMPOSE[@]}" ps

print_step "Confirm web container naming"
WEB_CONTAINER_ID="$("${COMPOSE[@]}" ps -q "${WEB_SERVICE}")"
WEB_CONTAINER_NAME="$(docker inspect -f '{{.Name}}' "${WEB_CONTAINER_ID}" | sed 's#^/##')"
echo "WEB_CONTAINER_NAME=${WEB_CONTAINER_NAME}"

if [[ "${WEB_CONTAINER_NAME}" != "${EXPECTED_WEB_CONTAINER_PREFIX}"* ]]; then
  echo "Expected web container name to start with ${EXPECTED_WEB_CONTAINER_PREFIX}, got ${WEB_CONTAINER_NAME}" >&2
  exit 1
fi

print_step "Confirm PostgreSQL image"
DB_CONTAINER_ID="$("${COMPOSE[@]}" ps -q "${DB_SERVICE}")"
DB_IMAGE_ACTUAL="$(docker inspect -f '{{.Config.Image}}' "${DB_CONTAINER_ID}")"
echo "DB_IMAGE=${DB_IMAGE_ACTUAL}"

if [[ "${DB_IMAGE_ACTUAL}" != "${EXPECTED_POSTGRES_IMAGE}" ]]; then
  echo "Expected DB image ${EXPECTED_POSTGRES_IMAGE}, got ${DB_IMAGE_ACTUAL}" >&2
  exit 1
fi

print_step "Wait for PostgreSQL to become ready"
wait_for_postgres

print_step "Verify Django can load local settings"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py check "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Verify migrations are up to date"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Apply database migrations"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py migrate --noinput "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Verify jobs app migrations are registered"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py showmigrations jobs "--settings=${DJANGO_SETTINGS_MODULE}"

print_step "Verify Sprint 2 Day 4 note route resolves through application detail"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from django.urls import reverse

expected_url = '/applications/1/'
actual_url = reverse('jobs:application_detail', kwargs={'pk': 1})
print(f'jobs:application_detail -> {actual_url}')
if actual_url != expected_url:
    raise SystemExit(f'Expected jobs:application_detail to resolve to {expected_url}, got {actual_url}')
"

print_step "Verify note model, note form, factory, and detail view import cleanly"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from apps.jobs.factories import ApplicationNoteFactory
from apps.jobs.forms import ApplicationNoteForm
from apps.jobs.models import ApplicationNote
from apps.jobs.models import JobApplication
from apps.jobs.views import application_detail

print(ApplicationNote.__name__)
print(ApplicationNoteFactory.__name__)
print(ApplicationNoteForm.__name__)
print(JobApplication.__name__)
print(application_detail.__name__)
"

print_step "Verify ApplicationNote field and relationship contract"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from apps.jobs.models import ApplicationNote

fields = {field.name for field in ApplicationNote._meta.fields}
required_fields = {'id', 'application', 'body', 'created_at', 'updated_at'}

missing_fields = required_fields - fields
if missing_fields:
    raise SystemExit(f'Missing ApplicationNote fields: {sorted(missing_fields)}')

application_field = ApplicationNote._meta.get_field('application')
if application_field.remote_field.model.__name__ != 'JobApplication':
    raise SystemExit('ApplicationNote.application must point to JobApplication.')

if application_field.remote_field.on_delete.__name__ != 'CASCADE':
    raise SystemExit('ApplicationNote.application must cascade when the parent application is deleted.')

if application_field.remote_field.related_name != 'application_notes':
    raise SystemExit('ApplicationNote.application related_name must be application_notes.')

print('ApplicationNote fields verified.')
print('ApplicationNote -> JobApplication relationship verified.')
print('ApplicationNote related_name verified.')
"

print_step "Run Sprint 2 Day 4 note workflow tests"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  pytest apps/jobs/tests/test_notes.py -q

print_step "Run Sprint 2 Day 4 model regression tests"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  pytest apps/jobs/tests/test_models.py -q

print_step "Run Sprint 2 Day 4 application ownership regression tests"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  pytest apps/jobs/tests/test_job_views.py -q

print_step "Run Sprint 2 Day 4 combined verification"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  pytest \
  apps/jobs/tests/test_notes.py \
  apps/jobs/tests/test_models.py \
  apps/jobs/tests/test_job_views.py \
  -q

print_step "Run full jobs app regression check"
run "${COMPOSE[@]}" exec -T "${WEB_SERVICE}" \
  pytest apps/jobs -q

print_step "Sprint 2 Day 4 verification complete"

cat <<'EOF'
Expected receipt:
Application note workflow tests pass.
Full apps/jobs regression tests pass.

Verified:
- Docker Compose uses the trackly-job-applications-tracker-project project name.
- The web service is executed through Docker Compose.
- The web container name starts with trackly-job-applications-tracker-project-web.
- PostgreSQL image expectation is postgres:16-alpine.
- PostgreSQL readiness uses the trackly database and trackly_user defaults.
- PostgreSQL is ready before Django commands run.
- Django local settings load successfully.
- jobs migrations are present and up to date.
- database migrations apply non-interactively.
- Sprint 2 Day 4 note creation route is handled through /applications/<pk>/.
- ApplicationNote model imports cleanly.
- ApplicationNoteFactory imports cleanly.
- ApplicationNoteForm imports cleanly.
- application detail view imports cleanly.
- ApplicationNote has the expected fields.
- ApplicationNote links to JobApplication with cascade delete.
- ApplicationNote uses the application_notes related name.
- users can add notes to their own applications.
- blank notes are rejected.
- notes render on application detail.
- users cannot add notes to another user's application.
- note ownership is derived from the parent application.
- full jobs app regression coverage still passes.

Sprint 2 Day 4 application notes workflow verified.
EOF
