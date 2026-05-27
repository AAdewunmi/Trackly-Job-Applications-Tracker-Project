#!/usr/bin/env bash
set -euo pipefail

# Sprint 1 Day 4 console-only verification runbook.
#
# Execution:
#   chmod +x docs/sprint-runbook/sprint-1/sprint-1-day-4.sh
#   ./docs/sprint-runbook/sprint-1/sprint-1-day-4.sh
#
# Purpose:
#   Verify the Trackly signup, login, logout, and profile journey using the
#   same Docker Compose project, web image, PostgreSQL image, URL wiring,
#   templates, Trackly CSS, and Django test client flow used by the project.

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

print_step "Confirm required Sprint 1 Day 4 authentication and UI files exist"
test -f apps/users/forms.py
test -f apps/users/views.py
test -f apps/users/urls.py
test -f apps/users/tests/test_auth_views.py
test -f apps/users/tests/test_views.py
test -f templates/base.html
test -f templates/users/signup.html
test -f templates/users/login.html
test -f templates/users/profile.html
test -f static/css/theme.css
test -f config/urls.py

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

print_step "Confirm users auth URLs are registered"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.urls import reverse

routes = {
    "signup": reverse("users:signup"),
    "login": reverse("users:login"),
    "logout": reverse("users:logout"),
    "profile": reverse("users:profile"),
}

for name, path in routes.items():
    print(f"{name}={path}")

expected = {
    "signup": "/accounts/signup/",
    "login": "/accounts/login/",
    "logout": "/accounts/logout/",
    "profile": "/accounts/profile/",
}

if routes != expected:
    raise SystemExit(f"Unexpected auth routes: {routes}")
PY

print_step "Confirm authentication forms load with expected fields"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from apps.users.forms import EmailAuthenticationForm, SignUpForm

signup_form = SignUpForm()
login_form = EmailAuthenticationForm()

print(f"SIGNUP_FIELDS={','.join(signup_form.fields.keys())}")
print(f"LOGIN_FIELDS={','.join(login_form.fields.keys())}")

required_signup_fields = {"email", "first_name", "last_name", "password1", "password2"}
required_login_fields = {"username", "password"}

if set(signup_form.fields.keys()) != required_signup_fields:
    raise SystemExit("Signup form fields do not match Sprint 1 Day 4 expectations.")

if set(login_form.fields.keys()) != required_login_fields:
    raise SystemExit("Login form fields do not match Sprint 1 Day 4 expectations.")
PY

print_step "Confirm templates contain expected product copy and shared shell"
run grep -n "Create your Trackly account" templates/users/signup.html
run grep -n "Sign in to Trackly" templates/users/login.html
run grep -n "Your profile" templates/users/profile.html
run grep -n "A focused workspace for job applications" templates/base.html
run grep -n "htmx.org" templates/base.html
run grep -n "theme.css" templates/base.html

print_step "Confirm stylesheet contains reusable Trackly UI rules"
run grep -n ".tl-card" static/css/theme.css
run grep -n ".tl-button" static/css/theme.css
run grep -n ".tl-form" static/css/theme.css
run grep -n ".tl-auth-shell" static/css/theme.css
run grep -n ".tl-auth-card" static/css/theme.css

print_step "Verify signup, login, profile, and logout with Django test client"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()
client = Client(HTTP_HOST="localhost")

signup_get = client.get(reverse("users:signup"))
print(f"SIGNUP_GET={signup_get.status_code}")

if signup_get.status_code != 200:
    raise SystemExit("Signup page did not load.")

email = "sprint1.day4@example.com"
User.objects.filter(email=email).delete()

signup_post = client.post(
    reverse("users:signup"),
    data={
        "email": email,
        "first_name": "Sprint",
        "last_name": "Four",
        "password1": "StrongPass12345!",
        "password2": "StrongPass12345!",
    },
)

print(f"SIGNUP_POST={signup_post.status_code}")
print(f"SIGNUP_REDIRECT={signup_post.headers.get('Location')}")

if signup_post.status_code != 302:
    raise SystemExit("Signup did not redirect after successful account creation.")

if signup_post.headers.get("Location") != reverse("dashboard:user"):
    raise SystemExit("Signup did not redirect to the user dashboard.")

created_user_exists = User.objects.filter(email=email).exists()
print(f"USER_CREATED={created_user_exists}")

if not created_user_exists:
    raise SystemExit("Signup did not create the expected user.")

profile_get = client.get(reverse("users:profile"))
print(f"PROFILE_GET_AUTHENTICATED={profile_get.status_code}")

if profile_get.status_code != 200:
    raise SystemExit("Authenticated profile page did not load.")

logout_post = client.post(reverse("users:logout"))
print(f"LOGOUT_POST={logout_post.status_code}")
print(f"LOGOUT_REDIRECT={logout_post.headers.get('Location')}")

if logout_post.status_code != 302:
    raise SystemExit("Logout did not redirect.")

if logout_post.headers.get("Location") != reverse("users:login"):
    raise SystemExit("Logout did not redirect to login.")

profile_after_logout = client.get(reverse("users:profile"))
print(f"PROFILE_GET_AFTER_LOGOUT={profile_after_logout.status_code}")
print(f"PROFILE_AFTER_LOGOUT_REDIRECT={profile_after_logout.headers.get('Location')}")

if profile_after_logout.status_code != 302:
    raise SystemExit("Anonymous profile access did not redirect.")

login_post = client.post(
    reverse("users:login"),
    data={
        "username": email,
        "password": "StrongPass12345!",
    },
)

print(f"LOGIN_POST={login_post.status_code}")
print(f"LOGIN_REDIRECT={login_post.headers.get('Location')}")

if login_post.status_code != 302:
    raise SystemExit("Login did not redirect after valid credentials.")

if login_post.headers.get("Location") != reverse("dashboard:user"):
    raise SystemExit("Login did not redirect to the user dashboard.")
PY

print_step "Run Sprint 1 Day 4 authentication view tests"
run "${COMPOSE[@]}" exec -T web pytest apps/users/tests/test_auth_views.py -q

print_step "Run all user tests after auth flow implementation"
run "${COMPOSE[@]}" exec -T web pytest apps/users -q

print_step "Run final Sprint 1 Day 4 receipt"
run "${COMPOSE[@]}" exec -T web python manage.py check --database default --settings=config.settings.local
echo "Sprint 1 Day 4 signup login logout and profile flow verified"
