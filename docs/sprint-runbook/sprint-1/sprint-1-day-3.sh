#!/usr/bin/env bash
set -euo pipefail

# Sprint 1 Day 3 console-only verification runbook.
#
# Purpose:
#   Verify Trackly's custom user model, roles foundation, repeatable identity
#   test data, and local Docker baseline.
#
# Run from the repository root:
#   chmod +x docs/sprint-runbook/sprint-1/sprint-1-day-3.sh
#   ./docs/sprint-runbook/sprint-1/sprint-1-day-3.sh
#
# Expected final receipt:
#   System check identified no issues (0 silenced).
#   Sprint 1 Day 3 custom user and roles foundation verified
#
# Notes:
#   This runbook intentionally uses the repository's default Docker Compose
#   project name so the web image remains:
#     trackly-job-applications-tracker-project-web
#   It verifies migrations with --check --dry-run and does not create migration
#   files during the verification run.

PROJECT_NAME="trackly-job-applications-tracker-project"
WEB_IMAGE_NAME="trackly-job-applications-tracker-project-web"
DB_IMAGE_NAME="postgres:16-alpine"

export POSTGRES_DB="${POSTGRES_DB:-trackly}"
export POSTGRES_USER="${POSTGRES_USER:-trackly_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-trackly_password}"

COMPOSE=(docker compose -p "${PROJECT_NAME}")

print_step() {
  echo
  echo "==> $1"
}

run() {
  echo
  echo "$ $*"
  "$@"
}

print_step "Confirm repository root"
pwd

print_step "Confirm required Sprint 1 Day 3 user and role files exist"
test -f apps/users/__init__.py
test -f apps/users/apps.py
test -f apps/users/models.py
test -f apps/users/admin.py
test -f apps/users/factories.py
test -f apps/users/tests/__init__.py
test -f apps/users/tests/test_models.py
test -f apps/roles/__init__.py
test -f apps/roles/apps.py
test -f apps/roles/models.py
test -f apps/roles/admin.py
test -f apps/roles/factories.py
test -f apps/roles/tests/__init__.py
test -f apps/roles/tests/test_models.py
test -f config/settings/base.py

print_step "Confirm Docker Compose project and PostgreSQL image configuration"
echo
echo "$ ${COMPOSE[*]} config | grep -E \"^(name:|  db:|  web:|    build:|    image: ${DB_IMAGE_NAME})|POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD\""
"${COMPOSE[@]}" config | grep -E "^(name:|  db:|  web:|    build:|    image: ${DB_IMAGE_NAME})|POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD"

print_step "Start the same Docker Compose web and database services"
run "${COMPOSE[@]}" up -d db web

print_step "Confirm containers are running under the expected project"
run "${COMPOSE[@]}" ps

print_step "Confirm running service names"
run "${COMPOSE[@]}" ps --services

print_step "Confirm PostgreSQL image is postgres:16-alpine"
DB_CONTAINER_ID="$("${COMPOSE[@]}" ps -q db)"
DB_IMAGE_ACTUAL="$(docker inspect -f '{{.Config.Image}}' "${DB_CONTAINER_ID}")"
echo "DB_IMAGE=${DB_IMAGE_ACTUAL}"
if [[ "${DB_IMAGE_ACTUAL}" != "${DB_IMAGE_NAME}" ]]; then
  echo "Expected DB image ${DB_IMAGE_NAME}, got ${DB_IMAGE_ACTUAL}"
  exit 1
fi

print_step "Confirm web image belongs to the Trackly project"
WEB_CONTAINER_ID="$("${COMPOSE[@]}" ps -q web)"
WEB_IMAGE_ACTUAL="$(docker inspect -f '{{.Config.Image}}' "${WEB_CONTAINER_ID}")"
echo "WEB_IMAGE=${WEB_IMAGE_ACTUAL}"
if [[ "${WEB_IMAGE_ACTUAL}" != "${WEB_IMAGE_NAME}" ]]; then
  echo "Expected web image ${WEB_IMAGE_NAME}, got ${WEB_IMAGE_ACTUAL}"
  exit 1
fi

print_step "Wait for PostgreSQL to become ready"
for attempt in {1..20}; do
  if "${COMPOSE[@]}" exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    echo "PostgreSQL is ready after ${attempt} attempt(s)."
    break
  fi

  if [[ "${attempt}" -eq 20 ]]; then
    echo "PostgreSQL did not become ready."
    exit 1
  fi

  sleep 1
done

print_step "Confirm PostgreSQL accepts connections"
run "${COMPOSE[@]}" exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

print_step "Confirm users and roles apps are installed"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.apps import apps

for app_label in ["roles", "users"]:
    app_config = apps.get_app_config(app_label)
    print(f"{app_label}={app_config.name}")
PY

print_step "Confirm AUTH_USER_MODEL uses the Trackly custom user"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

user_model = get_user_model()

print(f"AUTH_USER_MODEL={settings.AUTH_USER_MODEL}")
print(f"USER_MODEL={user_model.__module__}.{user_model.__name__}")

if settings.AUTH_USER_MODEL != "users.User":
    raise SystemExit("Expected AUTH_USER_MODEL to be users.User.")
PY

print_step "Run Django system check before migrations"
run "${COMPOSE[@]}" exec -T web python manage.py check --settings=config.settings.local

print_step "Verify role and user migrations are already present"
run "${COMPOSE[@]}" exec -T web python manage.py makemigrations roles users --check --dry-run --settings=config.settings.local

print_step "Apply migrations"
run "${COMPOSE[@]}" exec -T web python manage.py migrate --settings=config.settings.local

print_step "Show roles and users migration state"
run "${COMPOSE[@]}" exec -T web python manage.py showmigrations roles users --settings=config.settings.local

print_step "Confirm custom user table and role table exist in PostgreSQL"
run "${COMPOSE[@]}" exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "\dt users_user"
run "${COMPOSE[@]}" exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "\dt roles_role"

print_step "Confirm user and role models persist data"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.contrib.auth import get_user_model

from apps.roles.models import Role

User = get_user_model()

role, _ = Role.objects.get_or_create(
    code=Role.Codes.MEMBER,
    defaults={
        "name": "Member",
        "description": "Standard Trackly product user role.",
    },
)

user, created = User.objects.get_or_create(
    email="sprint1.day3@example.com",
    defaults={
        "first_name": "Sprint",
        "last_name": "Three",
    },
)

if created:
    user.set_password("StrongPass12345!")
    user.save(update_fields=["password"])

user.roles.add(role)

user_has_role = user.roles.filter(code=role.code).exists()

print(f"USER={user.email}")
print(f"ROLE={role.code}")
print(f"USER_HAS_ROLE={user_has_role}")

if not user_has_role:
    raise SystemExit("Expected user to have member role.")
PY

print_step "Run role model tests"
run "${COMPOSE[@]}" exec -T web pytest apps/roles -q

print_step "Run user model tests"
run "${COMPOSE[@]}" exec -T web pytest apps/users -q

print_step "Run combined Sprint 1 Day 3 identity tests"
run "${COMPOSE[@]}" exec -T web pytest apps/users apps/roles -q

print_step "Run final Sprint 1 Day 3 receipt"
run "${COMPOSE[@]}" exec -T web python manage.py check --database default --settings=config.settings.local
echo "Sprint 1 Day 3 custom user and roles foundation verified"
