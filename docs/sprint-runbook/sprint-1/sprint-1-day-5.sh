#!/usr/bin/env bash
set -euo pipefail

# Sprint 1 Day 5 console-only verification runbook.
#
# Execution:
#   chmod +x docs/sprint-runbook/sprint-1/sprint-1-day-5.sh
#   ./docs/sprint-runbook/sprint-1/sprint-1-day-5.sh
#
# Purpose:
#   Verify the Trackly authenticated user dashboard, protected admin dashboard,
#   role-aware permissions, URL wiring, templates, Docker Compose services, and
#   current automated test coverage using only console commands.

PROJECT_NAME="trackly-job-applications-tracker-project"
WEB_IMAGE_NAME="trackly-job-applications-tracker-project-web"
DB_IMAGE_NAME="postgres:16-alpine"

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

print_step "Confirm required Sprint 1 Day 5 dashboard, permission, and documentation files exist"
test -f apps/dashboard/__init__.py
test -f apps/dashboard/apps.py
test -f apps/dashboard/views.py
test -f apps/dashboard/urls.py
test -f apps/dashboard/tests/__init__.py
test -f apps/dashboard/tests/test_dashboard_views.py
test -f apps/roles/permissions.py
test -f apps/roles/tests/test_permissions.py
test -f config/tests/test_home_view.py
test -f templates/dashboard/user_index.html
test -f templates/dashboard/admin_index.html
test -f templates/base.html
test -f static/css/theme.css
test -f docs/design-system.md
test -f docs/architecture.md
test -f config/urls.py
test -f pytest.ini

print_step "Confirm Docker Compose project and PostgreSQL image configuration"
run "${COMPOSE[@]}" config | grep -E "^(name:|  db:|  web:|    build:|    image: postgres:16-alpine)|POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD"

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
  if "${COMPOSE[@]}" exec -T db pg_isready -U trackly_user -d trackly >/dev/null 2>&1; then
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
run "${COMPOSE[@]}" exec -T db pg_isready -U trackly_user -d trackly

print_step "Confirm local settings pass Django system check"
run "${COMPOSE[@]}" exec -T web python manage.py check --settings=config.settings.local

print_step "Confirm migrations are applied"
run "${COMPOSE[@]}" exec -T web python manage.py migrate --settings=config.settings.local

print_step "Confirm dashboard URLs are registered"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.urls import reverse

routes = {
    "user_dashboard": reverse("dashboard:user"),
    "admin_dashboard": reverse("dashboard:admin"),
}

for name, path in routes.items():
    print(f"{name}={path}")

expected = {
    "user_dashboard": "/dashboard/",
    "admin_dashboard": "/dashboard/admin/",
}

if routes != expected:
    raise SystemExit(f"Unexpected dashboard routes: {routes}")
PY

print_step "Confirm dashboard app and permission helper import correctly"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.apps import apps
from apps.roles.permissions import is_trackly_admin, user_has_role

dashboard_config = apps.get_app_config("dashboard")

print(f"dashboard={dashboard_config.name}")
print(f"is_trackly_admin={is_trackly_admin.__name__}")
print(f"user_has_role={user_has_role.__name__}")
PY

print_step "Confirm dashboard templates contain product dashboard copy"
run bash -lc "grep -niE 'dashboard|job search|application|workspace|command centre|command center' templates/dashboard/user_index.html | head -20"
run bash -lc "grep -niE 'admin|dashboard|platform|users|roles' templates/dashboard/admin_index.html | head -20"

print_step "Confirm base template links authenticated dashboard navigation"
run bash -lc "grep -n \"dashboard:user\\|users:profile\\|users:logout\" templates/base.html"

print_step "Confirm documentation describes dashboard and role-aware UI patterns"
run bash -lc "grep -niE 'dashboard|admin|role|protected|navigation' docs/design-system.md docs/architecture.md | head -40"

print_step "Verify dashboard access rules with Django test client"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

# The non-admin admin-dashboard probe intentionally produces a 403. Suppress
# Django's request logger here so the expected denial does not print a traceback.
logging.getLogger("django.request").setLevel(logging.CRITICAL)

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.roles.models import Role

User = get_user_model()

User.objects.filter(email__in=[
    "sprint1.day5.member@example.com",
    "sprint1.day5.staff@example.com",
    "sprint1.day5.roleadmin@example.com",
]).delete()

admin_role, _ = Role.objects.update_or_create(
    code=Role.Codes.ADMIN,
    defaults={
        "name": "Admin",
        "description": "Trackly product administrator role.",
        "is_active": True,
    },
)

member = User.objects.create_user(
    email="sprint1.day5.member@example.com",
    password="StrongPass12345!",
    first_name="Member",
    last_name="User",
)

staff_user = User.objects.create_user(
    email="sprint1.day5.staff@example.com",
    password="StrongPass12345!",
    first_name="Staff",
    last_name="User",
    is_staff=True,
)

role_admin = User.objects.create_user(
    email="sprint1.day5.roleadmin@example.com",
    password="StrongPass12345!",
    first_name="Role",
    last_name="Admin",
)
role_admin.roles.add(admin_role)

anonymous_client = Client(HTTP_HOST="localhost")

dashboard_anonymous = anonymous_client.get(reverse("dashboard:user"))
print(f"DASHBOARD_ANONYMOUS={dashboard_anonymous.status_code}")
print(f"DASHBOARD_ANONYMOUS_REDIRECT={dashboard_anonymous.headers.get('Location')}")

if dashboard_anonymous.status_code != 302:
    raise SystemExit("Anonymous dashboard access should redirect.")

admin_anonymous = anonymous_client.get(reverse("dashboard:admin"))
print(f"ADMIN_ANONYMOUS={admin_anonymous.status_code}")
print(f"ADMIN_ANONYMOUS_REDIRECT={admin_anonymous.headers.get('Location')}")

if admin_anonymous.status_code != 302:
    raise SystemExit("Anonymous admin dashboard access should redirect.")

member_client = Client(HTTP_HOST="localhost")
member_client.force_login(member)

dashboard_member = member_client.get(reverse("dashboard:user"))
print(f"DASHBOARD_MEMBER={dashboard_member.status_code}")

if dashboard_member.status_code != 200:
    raise SystemExit("Authenticated member dashboard access should return 200.")

admin_member = member_client.get(reverse("dashboard:admin"))
print(f"ADMIN_MEMBER={admin_member.status_code}")

if admin_member.status_code != 403:
    raise SystemExit("Non-admin member should receive 403 on admin dashboard.")

staff_client = Client(HTTP_HOST="localhost")
staff_client.force_login(staff_user)

admin_staff = staff_client.get(reverse("dashboard:admin"))
print(f"ADMIN_STAFF={admin_staff.status_code}")

if admin_staff.status_code != 200:
    raise SystemExit("Staff user should access admin dashboard.")

role_admin_client = Client(HTTP_HOST="localhost")
role_admin_client.force_login(role_admin)

admin_role_user = role_admin_client.get(reverse("dashboard:admin"))
print(f"ADMIN_ROLE_USER={admin_role_user.status_code}")

if admin_role_user.status_code != 200:
    raise SystemExit("User with Trackly admin role should access admin dashboard.")
PY

print_step "Verify permission helper behaviour directly"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.contrib.auth import get_user_model

from apps.roles.models import Role
from apps.roles.permissions import is_trackly_admin, user_has_role

User = get_user_model()

admin_role, _ = Role.objects.update_or_create(
    code=Role.Codes.ADMIN,
    defaults={
        "name": "Admin",
        "description": "Trackly product administrator role.",
        "is_active": True,
    },
)

member_role, _ = Role.objects.update_or_create(
    code=Role.Codes.MEMBER,
    defaults={
        "name": "Member",
        "description": "Standard Trackly product user role.",
        "is_active": True,
    },
)

admin_user, _ = User.objects.get_or_create(
    email="sprint1.day5.permission.admin@example.com",
    defaults={
        "first_name": "Permission",
        "last_name": "Admin",
    },
)
admin_user.roles.add(admin_role)

member_user, _ = User.objects.get_or_create(
    email="sprint1.day5.permission.member@example.com",
    defaults={
        "first_name": "Permission",
        "last_name": "Member",
    },
)
member_user.roles.add(member_role)

print(f"ADMIN_USER_HAS_ADMIN_ROLE={user_has_role(admin_user, Role.Codes.ADMIN)}")
print(f"ADMIN_USER_IS_TRACKLY_ADMIN={is_trackly_admin(admin_user)}")
print(f"MEMBER_USER_HAS_MEMBER_ROLE={user_has_role(member_user, Role.Codes.MEMBER)}")
print(f"MEMBER_USER_IS_TRACKLY_ADMIN={is_trackly_admin(member_user)}")

if not user_has_role(admin_user, Role.Codes.ADMIN):
    raise SystemExit("Expected admin user to have admin role.")

if not is_trackly_admin(admin_user):
    raise SystemExit("Expected admin role user to be treated as Trackly admin.")

if not user_has_role(member_user, Role.Codes.MEMBER):
    raise SystemExit("Expected member user to have member role.")

if is_trackly_admin(member_user):
    raise SystemExit("Member user should not be treated as Trackly admin.")
PY

print_step "Run Sprint 1 Day 5 dashboard integration tests"
run "${COMPOSE[@]}" exec -T web pytest apps/dashboard/tests/test_dashboard_views.py -q

print_step "Run role permission tests"
run "${COMPOSE[@]}" exec -T web pytest apps/roles/tests/test_permissions.py -q

print_step "Run home page tests"
run "${COMPOSE[@]}" exec -T web pytest config/tests/test_home_view.py -q

print_step "Run full Sprint 1 test suite"
run "${COMPOSE[@]}" exec -T web pytest -q

print_step "Run final Sprint 1 Day 5 receipt"
run "${COMPOSE[@]}" exec -T web python manage.py check --database default --settings=config.settings.local
echo "Sprint 1 Day 5 dashboard shell access control and integration tests verified"
