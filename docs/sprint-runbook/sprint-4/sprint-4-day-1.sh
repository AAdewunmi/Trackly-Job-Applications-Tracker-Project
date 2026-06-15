#!/usr/bin/env bash
#
# Sprint 4 Day 1 console-only verification runbook for Trackly.
#
# Purpose:
# Verify the Monday Sprint 4 DevOps baseline:
# - production-minded Dockerfile
# - Docker Compose web/PostgreSQL workflow
# - PostgreSQL readiness healthcheck
# - deterministic role and showcase demo-data seed commands
# - Makefile developer workflow shortcuts
# - documentation alignment
# - seed-data tests and full project regression suite
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
# Execution:
# chmod +x docs/sprint-runbook/sprint-4/sprint-4-day-1.sh
# ./docs/sprint-runbook/sprint-4/sprint-4-day-1.sh

set -Eeuo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly-job-applications-tracker-project}"
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"
EXPECTED_WEB_CONTAINER_PREFIX="${EXPECTED_WEB_CONTAINER_PREFIX:-trackly-job-applications-tracker-project-web}"
EXPECTED_POSTGRES_IMAGE="${EXPECTED_POSTGRES_IMAGE:-postgres:16-alpine}"
EXPECTED_DEMO_USER_COUNT="${EXPECTED_DEMO_USER_COUNT:-4}"
EXPECTED_APPLICATION_COUNT="${EXPECTED_APPLICATION_COUNT:-10}"
EXPECTED_NOTE_COUNT="${EXPECTED_NOTE_COUNT:-10}"
EXPECTED_TARGET_PROFILE_COUNT="${EXPECTED_TARGET_PROFILE_COUNT:-4}"
EXPECTED_INSIGHT_COUNT="${EXPECTED_INSIGHT_COUNT:-10}"

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

require_file() {
  local file_path="$1"

  if [[ ! -f "$file_path" ]]; then
    printf 'Required file missing: %s\n' "$file_path" >&2
    exit 1
  fi
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Required command missing: %s\n' "$command_name" >&2
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

assert_command_available_in_container() {
  local command_name="$1"

  print_command docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" sh -lc "command -v ${command_name}"
  compose_exec sh -lc "command -v ${command_name}"
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

assert_seed_counts() {
  print_section "Verify deterministic showcase seed counts"

  print_command docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python manage.py shell -c "<seed-count assertions>"
  compose_exec python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import ApplicationNote, JobApplication
from apps.roles.models import Role

User = get_user_model()
demo_emails = [
    'admin.demo@trackly.local',
    'user.demo@trackly.local',
    'analyst.demo@trackly.local',
    'empty.demo@trackly.local',
]
demo_member_emails = [
    'user.demo@trackly.local',
    'analyst.demo@trackly.local',
    'empty.demo@trackly.local',
]

demo_user_count = User.objects.filter(email__in=demo_emails).count()
demo_applications = JobApplication.objects.filter(owner__email__in=demo_member_emails)
application_count = demo_applications.count()
note_count = ApplicationNote.objects.filter(
    application__owner__email__in=demo_member_emails,
).count()
target_profile_count = TargetRoleProfile.objects.filter(
    owner__email__in=demo_member_emails,
).count()
insight_count = JobInsight.objects.filter(
    job_application__owner__email__in=demo_member_emails,
).count()
statuses = set(demo_applications.values_list('status', flat=True))
expected_statuses = set(JobApplication.Status.values)

print('DEMO_USER_COUNT=', demo_user_count)
print('APPLICATION_COUNT=', application_count)
print('NOTE_COUNT=', note_count)
print('TARGET_PROFILE_COUNT=', target_profile_count)
print('INSIGHT_COUNT=', insight_count)
print('STATUSES=', sorted(statuses))
print('ROLES=', sorted(Role.objects.values_list('code', flat=True)))

assert demo_user_count == int('$EXPECTED_DEMO_USER_COUNT')
assert application_count == int('$EXPECTED_APPLICATION_COUNT')
assert note_count == int('$EXPECTED_NOTE_COUNT')
assert target_profile_count == int('$EXPECTED_TARGET_PROFILE_COUNT')
assert insight_count == int('$EXPECTED_INSIGHT_COUNT')
assert expected_statuses.issubset(statuses)
assert Role.objects.filter(code=Role.Codes.ADMIN, is_active=True).exists()
assert Role.objects.filter(code=Role.Codes.MEMBER, is_active=True).exists()
"
}

print_section "Verify repository root"

require_file "manage.py"
require_file "Dockerfile"
require_file "docker-compose.yml"
require_file "Makefile"
require_file ".env.example"
require_file "requirements.txt"
require_file "README.md"
require_file "RUNBOOK.md"
require_file "docs/local-setup.md"
require_file "docs/architecture.md"
require_file "docs/domain-model.md"
require_file "docs/sprint-runbook/README.md"
require_file "apps/roles/management/commands/seed_roles.py"
require_file "apps/jobs/management/commands/seed_demo_data.py"
require_file "apps/jobs/tests/test_seed_demo_data.py"

printf 'Repository root verified: %s\n' "$(pwd)"

print_section "Verify required local commands"

require_command "docker"
require_command "grep"
require_command "sed"

run docker --version
run docker compose version

print_section "Verify Dockerfile production-minded baseline"

assert_file_contains "Dockerfile" "FROM python:3.12-slim" "Python slim base image"
assert_file_contains "Dockerfile" "PYTHONDONTWRITEBYTECODE=1" "Python bytecode setting"
assert_file_contains "Dockerfile" "PYTHONUNBUFFERED=1" "Python unbuffered output setting"
assert_file_contains "Dockerfile" "pip install --no-cache-dir -r /app/requirements.txt" "predictable dependency installation"
assert_file_contains "Dockerfile" "python -m playwright install chromium" "Playwright Chromium install"
assert_file_contains "Dockerfile" "python -m nltk.downloader" "NLTK runtime data install"
assert_file_contains "Dockerfile" "--settings=config.settings.local" "explicit local startup settings"
assert_file_contains "requirements.txt" "dj-database-url==" "database URL parser dependency"
assert_file_contains "requirements.txt" "gunicorn==" "production server dependency"

print_section "Verify Docker Compose workflow baseline"

assert_file_contains "docker-compose.yml" "dockerfile: Dockerfile" "explicit Dockerfile build config"
assert_file_contains "docker-compose.yml" 'WEB_PORT:-8000' "configurable web host port"
assert_file_contains "docker-compose.yml" 'POSTGRES_PORT:-5432' "configurable PostgreSQL host port"
assert_file_contains "docker-compose.yml" "condition: service_healthy" "database health-gated web startup"
assert_file_contains "docker-compose.yml" "pg_isready" "PostgreSQL healthcheck"
assert_file_contains "docker-compose.yml" "$EXPECTED_POSTGRES_IMAGE" "expected PostgreSQL image"

print_section "Verify seed workflow files and documentation"

assert_file_contains "Makefile" '$(MANAGE_T) seed_demo_data' "non-interactive make seed target"
assert_file_contains "README.md" "make seed" "README seed instruction"
assert_file_contains "RUNBOOK.md" "make seed" "runbook seed instruction"
assert_file_contains "docs/local-setup.md" "make seed" "local setup seed instruction"
assert_file_contains "docs/domain-model.md" "seed_demo_data" "domain demo data contract"
assert_file_contains "docs/architecture.md" "seed_demo_data" "architecture demo data workflow"
assert_file_contains "docs/sprint-runbook/README.md" "make seed" "sprint runbook seed instruction"

print_section "Build Docker images"

run docker compose -p "$COMPOSE_PROJECT_NAME" build

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

assert_command_available_in_container "python"
assert_command_available_in_container "pytest"

print_section "Run Django system check from web service"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python manage.py check

print_section "Run database migrations from web service"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python manage.py migrate --noinput

print_section "Seed baseline roles"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python manage.py seed_roles

print_section "Seed deterministic showcase demo data through Makefile"

run make seed

print_section "Re-run deterministic seed commands to prove idempotency"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python manage.py seed_roles
run make seed

assert_seed_counts

print_section "Run Sprint 4 Day 1 seed-data tests"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" pytest apps/jobs/tests/test_seed_demo_data.py -q

print_section "Run full project test suite"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" pytest -q

print_section "Run Ruff"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python -m ruff check .

print_section "Run Black check"

run docker compose -p "$COMPOSE_PROJECT_NAME" exec -T "$WEB_SERVICE" python -m black . --check

print_section "Sprint 4 Day 1 verification complete"

printf 'Verified Docker Compose project: %s\n' "$COMPOSE_PROJECT_NAME"
printf 'Verified web service: %s\n' "$WEB_SERVICE"
printf 'Verified web container prefix: %s\n' "$EXPECTED_WEB_CONTAINER_PREFIX"
printf 'Verified PostgreSQL image: %s\n' "$EXPECTED_POSTGRES_IMAGE"
printf 'Verified showcase demo users: %s\n' "$EXPECTED_DEMO_USER_COUNT"
printf 'Verified showcase applications: %s\n' "$EXPECTED_APPLICATION_COUNT"
printf 'Verified showcase notes: %s\n' "$EXPECTED_NOTE_COUNT"
printf 'Verified showcase target profiles: %s\n' "$EXPECTED_TARGET_PROFILE_COUNT"
printf 'Verified showcase insights: %s\n' "$EXPECTED_INSIGHT_COUNT"
printf 'Sprint 4 Day 1 Docker, Compose, and seed-data baseline passed.\n'
