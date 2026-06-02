#!/usr/bin/env bash
#
# Sprint 2 Day 5 console-only verification runbook for Trackly.
#
# Purpose:
# Verify the dashboard metrics workflow through the same Docker Compose web
# service used by local development. This script checks PostgreSQL readiness,
# Django configuration, migrations, URL contracts, selector/service imports,
# dashboard metric keys, template labels, focused tests, and regression tests.
#
# Expected Docker resources:
# - Compose project: trackly-job-applications-tracker-project
# - Web container prefix: trackly-job-applications-tracker-project-web
# - Database image: postgres:16-alpine
#
# Run from any directory:
# chmod +x docs/sprint-runbook/sprint-2/sprint-2-day-5.sh
# ./docs/sprint-runbook/sprint-2/sprint-2-day-5.sh

set -Eeuo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
EXPECTED_WEB_CONTAINER_PREFIX="${EXPECTED_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.local}"
EXPECTED_POSTGRES_IMAGE="${EXPECTED_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_USER="${POSTGRES_USER:-trackly_user}"
POSTGRES_DB="${POSTGRES_DB:-trackly}"

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

print_header "Confirm required Sprint 2 Day 5 files exist"

assert_file_exists "manage.py"
assert_file_exists "docker-compose.yml"
assert_file_exists "config/urls.py"
assert_file_exists "config/settings/base.py"
assert_file_exists "config/settings/local.py"

assert_directory_exists "apps"
assert_directory_exists "apps/jobs"
assert_file_exists "apps/jobs/apps.py"
assert_file_exists "apps/jobs/models.py"
assert_file_exists "apps/jobs/admin.py"
assert_file_exists "apps/jobs/forms.py"
assert_file_exists "apps/jobs/selectors.py"
assert_file_exists "apps/jobs/services.py"
assert_file_exists "apps/jobs/views.py"
assert_file_exists "apps/jobs/urls.py"
assert_file_exists "apps/jobs/factories.py"

assert_directory_exists "apps/dashboard"
assert_file_exists "apps/dashboard/apps.py"
assert_file_exists "apps/dashboard/services.py"
assert_file_exists "apps/dashboard/views.py"
assert_file_exists "apps/dashboard/urls.py"

assert_file_exists "apps/jobs/tests/test_models.py"
assert_file_exists "apps/jobs/tests/test_selectors.py"
assert_file_exists "apps/jobs/tests/test_services.py"
assert_file_exists "apps/jobs/tests/test_job_views.py"
assert_file_exists "apps/jobs/tests/test_job_update.py"
assert_file_exists "apps/jobs/tests/test_job_delete.py"
assert_file_exists "apps/jobs/tests/test_notes.py"
assert_file_exists "apps/dashboard/tests/test_dashboard_metrics.py"
assert_file_exists "apps/dashboard/tests/test_dashboard_views.py"

assert_directory_exists "templates"
assert_file_exists "templates/base.html"
assert_directory_exists "templates/jobs"
assert_file_exists "templates/jobs/application_list.html"
assert_file_exists "templates/jobs/application_form.html"
assert_file_exists "templates/jobs/application_detail.html"
assert_file_exists "templates/jobs/application_confirm_delete.html"
assert_directory_exists "templates/dashboard"
assert_file_exists "templates/dashboard/user_index.html"
assert_file_exists "templates/dashboard/admin_index.html"

assert_directory_exists "docs"
assert_file_exists "docs/domain-model.md"

print_header "Confirm Docker Compose project and service expectations"

printf "Docker Compose project name: %s\n" "${COMPOSE_PROJECT_NAME}"
printf "Expected web container prefix: %s\n" "${EXPECTED_WEB_CONTAINER_PREFIX}"
printf "Web service: %s\n" "${WEB_SERVICE}"
printf "Database service: %s\n" "${DB_SERVICE}"
printf "Expected PostgreSQL image: %s\n" "${EXPECTED_POSTGRES_IMAGE}"
printf "PostgreSQL readiness user: %s\n" "${POSTGRES_USER}"
printf "PostgreSQL readiness database: %s\n" "${POSTGRES_DB}"

run_command compose config --services

if ! compose config --services | grep -qx "${WEB_SERVICE}"; then
  printf "Expected Docker Compose service not found: %s\n" "${WEB_SERVICE}" >&2
  exit 1
fi

if ! compose config --services | grep -qx "${DB_SERVICE}"; then
  printf "Expected Docker Compose service not found: %s\n" "${DB_SERVICE}" >&2
  exit 1
fi

print_header "Start PostgreSQL and web services"

run_command compose up -d "${DB_SERVICE}" "${WEB_SERVICE}"

print_header "Confirm containers are running"

run_command compose ps

print_header "Confirm web container naming"

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

print_header "Wait for PostgreSQL to become ready"

wait_for_postgres

print_header "Verify Django can load local settings"

run_command compose exec -T "${WEB_SERVICE}" python manage.py check "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Verify migrations are up to date"

run_command compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Apply database migrations"

run_command compose exec -T "${WEB_SERVICE}" python manage.py migrate --noinput "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Verify jobs app migrations are registered"

run_command compose exec -T "${WEB_SERVICE}" python manage.py showmigrations jobs "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Verify Sprint 2 Day 5 URL names resolve"

run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from django.urls import reverse

expected_urls = {
    'dashboard:user': '/dashboard/',
    'dashboard:user-preview': '/dashboard/preview/',
    'jobs:application_list': '/applications/',
    'jobs:application_create': '/applications/new/',
}

for name, expected_url in expected_urls.items():
    actual_url = reverse(name)
    print(f'{name} -> {actual_url}')
    if actual_url != expected_url:
        raise SystemExit(f'Expected {name} to resolve to {expected_url}, got {actual_url}')
"

print_header "Verify dashboard metrics services and job selectors import cleanly"

run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from apps.dashboard.services import DashboardContext
from apps.dashboard.services import get_user_dashboard_context
from apps.dashboard.views import user_index
from apps.jobs.selectors import application_queryset_for_user
from apps.jobs.selectors import get_note_count_for_user
from apps.jobs.selectors import get_recent_applications_for_user
from apps.jobs.selectors import get_recent_applications_for_user_by_status
from apps.jobs.services import get_application_status_counts
from apps.jobs.services import get_user_pipeline_metrics

print(DashboardContext.__name__)
print(get_user_dashboard_context.__name__)
print(user_index.__name__)
print(application_queryset_for_user.__name__)
print(get_recent_applications_for_user.__name__)
print(get_recent_applications_for_user_by_status.__name__)
print(get_note_count_for_user.__name__)
print(get_application_status_counts.__name__)
print(get_user_pipeline_metrics.__name__)
"

print_header "Verify dashboard metric contract keys"

# Delete any previous probe account first so this verification is rerun-safe
# even if an earlier run stopped before cleanup.
run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from apps.jobs.services import get_user_pipeline_metrics
from apps.users.models import User

email = 'sprint2-day5-contract@example.com'
User.objects.filter(email=email).delete()
user = User.objects.create_user(
    email=email,
    password='ChangeMe12345',
)

try:
    metrics = get_user_pipeline_metrics(user)
    expected_keys = {
        'total_applications',
        'active_applications',
        'saved_jobs',
        'follow_ups',
        'interviews',
        'offers',
        'rejections',
        'notes',
    }

    print(metrics)

    missing_keys = expected_keys - set(metrics)
    extra_keys = set(metrics) - expected_keys

    if missing_keys:
        raise SystemExit(f'Missing metric keys: {sorted(missing_keys)}')

    if extra_keys:
        raise SystemExit(f'Unexpected metric keys: {sorted(extra_keys)}')

    for key, value in metrics.items():
        if value != 0:
            raise SystemExit(f'Expected empty dashboard metric {key} to be 0, got {value}')
finally:
    user.delete()

print('Dashboard metric contract verified.')
"

print_header "Verify dashboard template contains Sprint 2 labels"

run_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "
from pathlib import Path

template_path = Path('templates/dashboard/user_index.html')
content = template_path.read_text()

required_labels = [
    'Application Pipeline',
    'Application Tracker',
    'Progress Metrics',
    'AI/NLP Insights',
    'Saved jobs',
    'Follow-ups',
    'Interviews',
    'Saved',
    'Applied',
    'Interview',
    'Start tracking applications',
    'Total Applications',
    'Active Applications',
    'Offers',
    'Rejections',
    'Notes',
]

for label in required_labels:
    print(f'Checking label: {label}')
    if label not in content:
        raise SystemExit(f'Missing dashboard label: {label}')

print('Dashboard template labels verified.')
"

print_header "Run Sprint 2 Day 5 formatting and lint checks"

run_command compose exec -T "${WEB_SERVICE}" python -m black . --check
run_command compose exec -T "${WEB_SERVICE}" python -m ruff check .

print_header "Run Sprint 2 Day 5 dashboard metric tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/dashboard/tests/test_dashboard_metrics.py -q

print_header "Run Sprint 2 Day 5 dashboard view tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/dashboard/tests/test_dashboard_views.py -q

print_header "Run Sprint 2 Day 5 selector and service tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/jobs/tests/test_selectors.py apps/jobs/tests/test_services.py -q

print_header "Run Sprint 2 Day 5 jobs app regression tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/jobs -q

print_header "Run Sprint 2 Day 5 dashboard app regression tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/dashboard -q

print_header "Run Sprint 2 Day 5 full regression suite"

run_command compose exec -T "${WEB_SERVICE}" pytest -q

print_header "Sprint 2 Day 5 verification complete"

cat <<'EOF'
Expected receipt:
- Docker Compose uses the trackly-job-applications-tracker-project project name.
- The web container name starts with trackly-job-applications-tracker-project-web.
- PostgreSQL image is postgres:16-alpine.
- PostgreSQL is ready before Django commands run.
- Django local settings load successfully.
- jobs migrations are present and up to date.
- database migrations apply non-interactively.
- dashboard:user resolves to /dashboard/.
- dashboard:user-preview resolves to /dashboard/preview/.
- jobs application list and create URLs resolve correctly.
- DashboardContext and dashboard user_index import cleanly.
- user-scoped selectors and dashboard metric services import cleanly.
- dashboard metric contract contains existing and pipeline-specific keys.
- empty dashboard metrics default to zero.
- dashboard template renders application pipeline and progress metric labels.
- Black and Ruff checks pass.
- dashboard, selector, service, jobs app, and full regression tests pass.

Sprint 2 Day 5 dashboard metrics workflow verified.
EOF
