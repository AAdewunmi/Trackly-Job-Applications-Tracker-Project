#!/usr/bin/env bash

# Sprint 3 Day 4 console-only verification runbook.
#
# Purpose:
# - Verify the Thursday insight-generation browser workflow.
# - Verify the insight service remains idempotent and ownership-protected.
# - Verify the current admin dashboard/browser tooling additions are available.
#
# Execution:
#   chmod +x docs/sprint-runbook/sprint-3/sprint-3-day-4.sh
#   ./docs/sprint-runbook/sprint-3/sprint-3-day-4.sh

set -Eeuo pipefail

PROJECT_ROOT="/Users/adrianadewunmi/VSCODE/Trackly-Job-Applications-Tracker-Project"
COMPOSE_PROJECT_NAME="trackly-job-applications-tracker-project"
EXPECTED_WEB_CONTAINER_PREFIX="trackly-job-applications-tracker-project-web"
EXPECTED_DB_IMAGE="postgres:16-alpine"
WEB_SERVICE="web"
DB_SERVICE="db"
DJANGO_SETTINGS_MODULE="config.settings.local"

POSTGRES_READINESS_USER="${POSTGRES_USER:-trackly_user}"
POSTGRES_READINESS_DB="${POSTGRES_DB:-trackly}"

compose() {
  COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}" docker compose "$@"
}

section() {
  printf "\n==> %s\n\n" "$1"
}

run() {
  printf "$ %s\n" "$*"
  "$@"
}

run_compose() {
  printf "$ compose %s\n" "$*"
  compose "$@"
}

django_python() {
  printf "$ compose exec -T -e DJANGO_SETTINGS_MODULE=%s %s python - <python>\n" "${DJANGO_SETTINGS_MODULE}" "${WEB_SERVICE}"
  compose exec -T -e DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" "${WEB_SERVICE}" python -
}

assert_file_exists() {
  local file_path="$1"

  if [[ ! -f "${file_path}" ]]; then
    printf "Missing required file: %s\n" "${file_path}" >&2
    exit 1
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local failure_message="$3"

  if [[ "${haystack}" != *"${needle}"* ]]; then
    printf "%s\n" "${failure_message}" >&2
    printf "Expected to find: %s\n" "${needle}" >&2
    printf "Actual output:\n%s\n" "${haystack}" >&2
    exit 1
  fi
}

section "Confirm repository root"
run cd "${PROJECT_ROOT}"
run pwd

section "Confirm Sprint 3 Day 4 files exist"
assert_file_exists "apps/insights/forms.py"
assert_file_exists "apps/insights/services.py"
assert_file_exists "apps/insights/selectors.py"
assert_file_exists "apps/insights/views.py"
assert_file_exists "apps/insights/urls.py"
assert_file_exists "apps/insights/tests/test_insight_generation.py"
assert_file_exists "apps/insights/tests/test_insight_permissions.py"
assert_file_exists "apps/jobs/views.py"
assert_file_exists "templates/jobs/application_detail.html"
assert_file_exists "templates/insights/partials/job_insight_panel.html"
assert_file_exists "templates/insights/target_profile_form.html"
assert_file_exists "templates/dashboard/admin_index.html"
assert_file_exists "docs/design-system.md"

section "Confirm Docker Compose project and service expectations"
printf "Docker Compose project name: %s\n" "${COMPOSE_PROJECT_NAME}"
printf "Expected web container prefix: %s\n" "${EXPECTED_WEB_CONTAINER_PREFIX}"
printf "Web service: %s\n" "${WEB_SERVICE}"
printf "Database service: %s\n" "${DB_SERVICE}"
printf "Expected PostgreSQL image: %s\n" "${EXPECTED_DB_IMAGE}"
printf "PostgreSQL readiness user: %s\n" "${POSTGRES_READINESS_USER}"
printf "PostgreSQL readiness database: %s\n" "${POSTGRES_READINESS_DB}"

SERVICES_OUTPUT="$(compose config --services)"
printf "$ compose config --services\n%s\n" "${SERVICES_OUTPUT}"
assert_contains "${SERVICES_OUTPUT}" "${DB_SERVICE}" "Expected db service to exist."
assert_contains "${SERVICES_OUTPUT}" "${WEB_SERVICE}" "Expected web service to exist."

section "Build and start Docker services"
run_compose build "${WEB_SERVICE}"
run_compose up -d "${DB_SERVICE}" "${WEB_SERVICE}"

section "Confirm services are running"
run_compose ps

section "Confirm web container uses the expected Compose project prefix"
WEB_CONTAINER_NAME="$(compose ps -q "${WEB_SERVICE}" | xargs docker inspect --format '{{ .Name }}' | sed 's#^/##')"
printf "WEB_CONTAINER_NAME=%s\n" "${WEB_CONTAINER_NAME}"

if [[ "${WEB_CONTAINER_NAME}" != "${EXPECTED_WEB_CONTAINER_PREFIX}"* ]]; then
  printf "Expected web container name to start with %s, got %s\n" "${EXPECTED_WEB_CONTAINER_PREFIX}" "${WEB_CONTAINER_NAME}" >&2
  exit 1
fi

section "Confirm PostgreSQL image"
DB_IMAGE="$(compose ps -q "${DB_SERVICE}" | xargs docker inspect --format '{{ .Config.Image }}')"
printf "DB_IMAGE=%s\n" "${DB_IMAGE}"

if [[ "${DB_IMAGE}" != "${EXPECTED_DB_IMAGE}" ]]; then
  printf "Expected database image %s, got %s\n" "${EXPECTED_DB_IMAGE}" "${DB_IMAGE}" >&2
  exit 1
fi

section "Wait for PostgreSQL readiness"
for attempt in $(seq 1 30); do
  if compose exec -T "${DB_SERVICE}" pg_isready -U "${POSTGRES_READINESS_USER}" -d "${POSTGRES_READINESS_DB}" >/dev/null 2>&1; then
    printf "PostgreSQL is ready after %s attempt(s).\n" "${attempt}"
    break
  fi

  if [[ "${attempt}" == "30" ]]; then
    printf "PostgreSQL did not become ready.\n" >&2
    exit 1
  fi

  sleep 1
done

section "Verify Django system check"
run_compose exec -T "${WEB_SERVICE}" python manage.py check --settings="${DJANGO_SETTINGS_MODULE}"

section "Verify migrations are up to date"
run_compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run --settings="${DJANGO_SETTINGS_MODULE}"

section "Apply migrations"
run_compose exec -T "${WEB_SERVICE}" python manage.py migrate --noinput --settings="${DJANGO_SETTINGS_MODULE}"

section "Verify Sprint 3 Day 4 imports"
django_python <<'PY'
import django

django.setup()

from apps.insights.forms import JobInsightGenerationForm, TargetRoleProfileForm
from apps.insights.selectors import (
    get_active_target_profiles_for_user,
    get_insights_for_user,
    get_latest_insight_for_application,
    get_recent_insights_for_user,
    get_target_profiles_for_user,
)
from apps.insights.services import (
    build_job_source_text,
    build_target_source_text,
    calculate_source_hash,
    generate_job_insight,
)
from apps.insights.views import (
    GenerateJobInsightView,
    InsightListView,
    TargetRoleProfileCreateView,
)
from apps.dashboard.services import get_admin_dashboard_context

print(TargetRoleProfileForm.__name__)
print(JobInsightGenerationForm.__name__)
print(get_target_profiles_for_user.__name__)
print(get_active_target_profiles_for_user.__name__)
print(get_latest_insight_for_application.__name__)
print(get_insights_for_user.__name__)
print(get_recent_insights_for_user.__name__)
print(build_job_source_text.__name__)
print(build_target_source_text.__name__)
print(calculate_source_hash.__name__)
print(generate_job_insight.__name__)
print(InsightListView.__name__)
print(TargetRoleProfileCreateView.__name__)
print(GenerateJobInsightView.__name__)
print(get_admin_dashboard_context.__name__)
PY

section "Verify Sprint 3 Day 4 browser URL names and paths"
django_python <<'PY'
import django

django.setup()

from django.urls import reverse

expected_urls = {
    "insights:insight-list": "/insights/",
    "insights:target-profile-create": "/insights/target-profiles/new/",
    "jobs:application_list": "/applications/",
    "dashboard:admin": "/dashboard/admin/",
}

for name, expected_url in expected_urls.items():
    actual_url = reverse(name)
    print(f"{name} -> {actual_url}")
    if actual_url != expected_url:
        raise SystemExit(f"Expected {name} to resolve to {expected_url}, got {actual_url}")

generate_url = reverse("insights:job-insight-generate", kwargs={"application_pk": 123})
application_detail_url = reverse("jobs:application_detail", kwargs={"pk": 123})
print(f"insights:job-insight-generate -> {generate_url}")
print(f"jobs:application_detail -> {application_detail_url}")

if generate_url != "/insights/applications/123/generate/":
    raise SystemExit(
        "Expected insights:job-insight-generate to resolve to "
        f"/insights/applications/123/generate/, got {generate_url}"
    )

if application_detail_url != "/applications/123/":
    raise SystemExit(
        "Expected jobs:application_detail to resolve to "
        f"/applications/123/, got {application_detail_url}"
    )
PY

section "Verify target profile form normalises keyword text"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model

from apps.insights.forms import TargetRoleProfileForm
from apps.insights.models import TargetRoleProfile

User = get_user_model()
User.objects.filter(email="day4.form@example.com").delete()
user = User.objects.create_user(
    email="day4.form@example.com",
    password="SmokePass12345",
    first_name="Day4",
    last_name="Form",
)

form = TargetRoleProfileForm(
    data={
        "title": "Backend Engineer",
        "description": "Python and Django backend role.",
        "keywords_text": "Python, Django, API, PostgreSQL, Docker, Testing, Python",
        "is_active": "on",
    }
)

print(form.is_valid())
print(form.errors)

if not form.is_valid():
    raise SystemExit("Expected target role profile form to be valid.")

profile = form.save(commit=False)
profile.owner = user
profile.save()

profile.refresh_from_db()
print(profile.keywords)

expected_keywords = ["python", "django", "api", "postgresql", "docker", "testing"]

if profile.keywords != expected_keywords:
    raise SystemExit(f"Expected keywords {expected_keywords}, got {profile.keywords}")

TargetRoleProfile.objects.filter(owner=user).delete()
user.delete()
PY

section "Verify insight generation form limits profiles to the current user"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.forms import JobInsightGenerationForm

User = get_user_model()
User.objects.filter(email__in=["day4.owner@example.com", "day4.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day4.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day4.other@example.com",
    password="SmokePass12345",
)

own_profile = TargetRoleProfileFactory(owner=owner, title="Own Backend Profile")
TargetRoleProfileFactory(owner=other, title="Other Backend Profile")

form = JobInsightGenerationForm(user=owner)
profile_ids = list(form.fields["target_profile"].queryset.values_list("id", flat=True))

print(profile_ids)

if own_profile.id not in profile_ids:
    raise SystemExit("Expected current user's profile to be available.")

if len(profile_ids) != 1:
    raise SystemExit("Expected only one current-user profile in the generation form.")
PY

section "Verify insight source text builders"
django_python <<'PY'
import django

django.setup()

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.services import build_job_source_text, build_target_source_text
from apps.jobs.factories import JobApplicationFactory

application = JobApplicationFactory(
    title="Backend Engineer",
    company="Trackly Labs",
    job_description="Python Django REST API PostgreSQL Docker testing.",
    notes="Prepare examples for API interview.",
)
profile = TargetRoleProfileFactory(
    title="Graduate Backend Engineer",
    description="Python and Django backend profile.",
    keywords=["python", "django", "api", "postgresql"],
)

job_source_text = build_job_source_text(application)
target_source_text = build_target_source_text(profile)

print(job_source_text)
print(target_source_text)

for expected in ["Backend Engineer", "Trackly Labs", "Python Django", "Prepare examples"]:
    if expected not in job_source_text:
        raise SystemExit(f"Expected job source text to include {expected}")

for expected in ["Graduate Backend Engineer", "Python and Django", "postgresql"]:
    if expected not in target_source_text:
        raise SystemExit(f"Expected target source text to include {expected}")
PY

section "Verify source hashing changes when job text changes"
django_python <<'PY'
import django

django.setup()

from apps.insights.services import calculate_source_hash

first = calculate_source_hash(
    job_source_text="Python Django API",
    target_source_text="Python Django API PostgreSQL",
)
second = calculate_source_hash(
    job_source_text="Python Django API Docker",
    target_source_text="Python Django API PostgreSQL",
)

print(first)
print(second)

if first == second:
    raise SystemExit("Expected source hash to change when job source text changes.")

if len(first) != 64 or len(second) != 64:
    raise SystemExit("Expected SHA-256 hashes to be 64 characters long.")
PY

section "Verify service generates and persists insight"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day4.service@example.com").delete()
user = User.objects.create_user(
    email="day4.service@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    title="Graduate Django Engineer",
    company="Trackly Labs",
    job_description="Python Django REST API PostgreSQL Docker testing.",
    notes="Prepare API examples.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    title="Backend Target",
    keywords=["python", "django", "api", "postgresql", "docker", "testing"],
)

result = generate_job_insight(
    user=user,
    application=application,
    target_profile=profile,
)

print(result.insight.id)
print(result.created)
print(result.insight.score_label)
print(result.insight.similarity_score)
print(result.insight.top_overlapping_terms)
print(result.insight.missing_target_terms)

if result.created is not True:
    raise SystemExit("Expected first service generation to create an insight.")

if not JobInsight.objects.filter(job_application=application, target_profile=profile).exists():
    raise SystemExit("Expected persisted JobInsight record.")

if result.insight.similarity_score <= 0:
    raise SystemExit("Expected positive similarity score for related text.")
PY

section "Verify repeated service generation reuses unchanged insight"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day4.idempotent@example.com").delete()
user = User.objects.create_user(
    email="day4.idempotent@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    job_description="Python Django PostgreSQL testing.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    keywords=["python", "django", "postgresql", "testing"],
)

first = generate_job_insight(
    user=user,
    application=application,
    target_profile=profile,
)
second = generate_job_insight(
    user=user,
    application=application,
    target_profile=profile,
)

print(first.insight.id)
print(second.insight.id)
print(JobInsight.objects.filter(job_application=application, target_profile=profile).count())

if first.created is not True:
    raise SystemExit("Expected first generation to create an insight.")

if second.created is not False:
    raise SystemExit("Expected second generation to reuse unchanged insight.")

if first.insight.id != second.insight.id:
    raise SystemExit("Expected unchanged generation to reuse the same insight id.")
PY

section "Verify service rejects cross-user application"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email__in=["day4.cross.owner@example.com", "day4.cross.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day4.cross.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day4.cross.other@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(owner=owner)
profile = TargetRoleProfileFactory(owner=other)

caught = False

try:
    generate_job_insight(
        user=other,
        application=application,
        target_profile=profile,
    )
except PermissionDenied:
    caught = True

print(caught)

if not caught:
    raise SystemExit("Expected PermissionDenied for another user's application.")
PY

section "Verify service rejects cross-user target profile"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email__in=["day4.profile.owner@example.com", "day4.profile.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day4.profile.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day4.profile.other@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(owner=owner)
profile = TargetRoleProfileFactory(owner=other)

caught = False

try:
    generate_job_insight(
        user=owner,
        application=application,
        target_profile=profile,
    )
except PermissionDenied:
    caught = True

print(caught)

if not caught:
    raise SystemExit("Expected PermissionDenied for another user's target profile.")
PY

section "Verify browser target profile creation workflow"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()
User.objects.filter(email="day4.browser.profile@example.com").delete()
user = User.objects.create_user(
    email="day4.browser.profile@example.com",
    password="SmokePass12345",
)

client = Client(HTTP_HOST="localhost")
client.force_login(user)

response = client.post(
    reverse("insights:target-profile-create"),
    {
        "title": "Browser Backend Target",
        "description": "Backend role with Django and APIs.",
        "keywords_text": "python, django, api, postgresql, docker",
        "is_active": "on",
    },
)

print(response.status_code)
print(response.url)
print(user.target_role_profiles.filter(title="Browser Backend Target").exists())

if response.status_code != 302:
    raise SystemExit("Expected target profile creation to redirect after success.")

if response.url != reverse("insights:insight-list"):
    raise SystemExit("Expected successful profile creation to redirect to insight list.")

if not user.target_role_profiles.filter(title="Browser Backend Target").exists():
    raise SystemExit("Expected target profile to be created for user.")
PY

section "Verify browser insight generation workflow"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day4.browser.generate@example.com").delete()
user = User.objects.create_user(
    email="day4.browser.generate@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    job_description="Python Django REST API PostgreSQL Docker testing.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    keywords=["python", "django", "api", "postgresql", "docker", "testing"],
)

client = Client(HTTP_HOST="localhost")
client.force_login(user)

response = client.post(
    reverse("insights:job-insight-generate", kwargs={"application_pk": application.pk}),
    {"target_profile": profile.pk},
)

print(response.status_code)
print(response.url)
print(JobInsight.objects.filter(job_application=application, target_profile=profile).exists())

if response.status_code != 302:
    raise SystemExit("Expected insight generation view to redirect after POST.")

if response.url != reverse("jobs:application_detail", kwargs={"pk": application.pk}):
    raise SystemExit("Expected generation view to redirect back to application detail.")

if not JobInsight.objects.filter(job_application=application, target_profile=profile).exists():
    raise SystemExit("Expected browser workflow to generate a stored insight.")
PY

section "Verify browser insight generation blocks another user's application"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email__in=["day4.browser.owner@example.com", "day4.browser.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day4.browser.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day4.browser.other@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(owner=owner)
profile = TargetRoleProfileFactory(owner=other)

client = Client(HTTP_HOST="localhost")
client.force_login(other)

response = client.post(
    reverse("insights:job-insight-generate", kwargs={"application_pk": application.pk}),
    {"target_profile": profile.pk},
)

print(response.status_code)
print(JobInsight.objects.filter(job_application=application).count())

if response.status_code != 404:
    raise SystemExit("Expected 404 for another user's application.")

if JobInsight.objects.filter(job_application=application).exists():
    raise SystemExit("Expected no insight to be created for another user's application.")
PY

section "Verify application detail page contains insight generation UI"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.insights.factories import TargetRoleProfileFactory
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day4.detail@example.com").delete()
user = User.objects.create_user(
    email="day4.detail@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    job_description="Python Django REST API PostgreSQL Docker testing.",
)
TargetRoleProfileFactory(owner=user, title="Detail Backend Target")

client = Client(HTTP_HOST="localhost")
client.force_login(user)

response = client.get(reverse("jobs:application_detail", kwargs={"pk": application.pk}))

print(response.status_code)

content = response.content.decode("utf-8")

for expected in ["Generate job insight", "Target role profile", "Generate insight"]:
    if expected not in content:
        raise SystemExit(f"Expected application detail page to contain {expected}")

if response.status_code != 200:
    raise SystemExit("Expected application detail page to render successfully.")
PY

section "Verify latest insight appears on application detail page"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day4.detail.insight@example.com").delete()
user = User.objects.create_user(
    email="day4.detail.insight@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    job_description="Python Django REST API PostgreSQL Docker testing.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    title="Backend Detail Target",
    keywords=["python", "django", "api", "postgresql", "docker", "testing"],
)
generate_job_insight(
    user=user,
    application=application,
    target_profile=profile,
)

client = Client(HTTP_HOST="localhost")
client.force_login(user)

response = client.get(reverse("jobs:application_detail", kwargs={"pk": application.pk}))
content = response.content.decode("utf-8")

print(response.status_code)

for expected in ["Latest score", "Target profile", "Overlap terms", "Missing terms"]:
    if expected not in content:
        raise SystemExit(f"Expected latest insight summary to contain {expected}")

if response.status_code != 200:
    raise SystemExit("Expected application detail page with insight to render successfully.")
PY

section "Verify admin login redirect and dashboard service context"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.dashboard.services import get_admin_dashboard_context

User = get_user_model()
email = "day4.admin@example.com"
User.objects.filter(email=email).delete()
admin = User.objects.create_superuser(
    email=email,
    password="SmokePass12345",
)

client = Client(HTTP_HOST="localhost")
response = client.post(
    reverse("users:login"),
    {"username": email, "password": "SmokePass12345"},
)

print(response.status_code)
print(response.url)

if response.status_code != 302:
    raise SystemExit("Expected admin login to redirect.")

if response.url != reverse("dashboard:admin"):
    raise SystemExit("Expected admin login to redirect to admin dashboard.")

context = get_admin_dashboard_context()
print(context.total_users)
print(context.total_applications)
print(context.application_page.paginator.count)

admin.delete()
PY

section "Verify Playwright and admin dashboard browser rendering"
run_compose exec -T "${WEB_SERVICE}" python -m playwright --version

django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
admin, _ = User.objects.get_or_create(email="admin@trackly.local")
admin.is_staff = True
admin.is_superuser = True
admin.is_active = True
admin.set_password("password123")
admin.save()
print(admin.email)
PY

run_compose exec -T "${WEB_SERVICE}" python - <<'PY'
from pathlib import Path

from playwright.sync_api import sync_playwright

screenshot_path = Path("/app/static/admin-dashboard-day4-runbook.png")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    page.goto("http://localhost:8000/accounts/login/", wait_until="networkidle")
    page.fill('input[name="username"]', "admin@trackly.local")
    page.fill('input[name="password"]', "password123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard/admin/", timeout=10000)

    css_href = page.locator('link[rel="stylesheet"]').first.get_attribute("href")
    workspace_display = page.locator(".tl-admin-workspace").evaluate(
        "el => getComputedStyle(el).display"
    )
    dashboard_columns = page.locator(".tl-admin-dashboard-grid").evaluate(
        "el => getComputedStyle(el).gridTemplateColumns"
    )
    page.screenshot(path=str(screenshot_path), full_page=True)
    browser.close()

print(css_href)
print(workspace_display)
print(dashboard_columns)
print(screenshot_path)

if "20260611-admin-dashboard-01" not in css_href:
    raise SystemExit("Expected admin dashboard CSS cache-buster to be loaded.")

if workspace_display != "grid":
    raise SystemExit("Expected admin dashboard workspace to render as a CSS grid.")

if " " not in dashboard_columns:
    raise SystemExit("Expected admin dashboard overview/activity grid columns.")
PY

section "Run Sprint 3 Day 4 insight generation tests"
run_compose exec -T "${WEB_SERVICE}" pytest apps/insights/tests/test_insight_generation.py -q

section "Run Sprint 3 Day 4 browser permission tests"
run_compose exec -T "${WEB_SERVICE}" pytest apps/insights/tests/test_insight_permissions.py -q

section "Run Sprint 3 Day 4 test subset"
run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/insights/tests/test_insight_generation.py \
  apps/insights/tests/test_insight_permissions.py \
  -q

section "Run dashboard and auth regression subset"
run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/dashboard/tests/test_dashboard_metrics.py \
  apps/dashboard/tests/test_dashboard_views.py \
  apps/users/tests/test_views.py \
  -q

section "Run all insights tests after Thursday workflow changes"
run_compose exec -T "${WEB_SERVICE}" pytest apps/insights -q

section "Run focused style checks for Thursday Python files"
run_compose exec -T "${WEB_SERVICE}" python -m ruff check \
  apps/insights/forms.py \
  apps/insights/services.py \
  apps/insights/selectors.py \
  apps/insights/views.py \
  apps/insights/urls.py \
  apps/insights/tests/test_insight_generation.py \
  apps/insights/tests/test_insight_permissions.py \
  apps/jobs/views.py \
  apps/dashboard/services.py \
  apps/dashboard/views.py \
  apps/users/views.py

run_compose exec -T "${WEB_SERVICE}" python -m black \
  apps/insights/forms.py \
  apps/insights/services.py \
  apps/insights/selectors.py \
  apps/insights/views.py \
  apps/insights/urls.py \
  apps/insights/tests/test_insight_generation.py \
  apps/insights/tests/test_insight_permissions.py \
  apps/jobs/views.py \
  apps/dashboard/services.py \
  apps/dashboard/views.py \
  apps/users/views.py \
  --check

section "Verify templates and docs contain expected workflow labels"
run grep -i "Generate job insight" templates/jobs/application_detail.html
run grep -i "Create target profile" templates/insights/target_profile_form.html
run grep -i "Latest insight" templates/insights/partials/job_insight_panel.html
run grep -i "Top overlapping terms" templates/insights/partials/job_insight_panel.html
run grep -i "Missing or weaker target terms" templates/insights/partials/job_insight_panel.html
run grep -i "Platform overview" templates/dashboard/admin_index.html
run grep -i "Control centre" templates/dashboard/admin_index.html
run grep -i "Playwright" docs/design-system.md

section "Run final Sprint 3 Day 4 verification receipt"
run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/insights/tests/test_insight_generation.py \
  apps/insights/tests/test_insight_permissions.py \
  -q

run_compose exec -T "${WEB_SERVICE}" pytest apps/insights -q

run_compose exec -T "${WEB_SERVICE}" python manage.py check --settings="${DJANGO_SETTINGS_MODULE}"

run_compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run --settings="${DJANGO_SETTINGS_MODULE}"

section "Sprint 3 Day 4 verification complete"
cat <<'EOF'
Completion checkpoint:
- Docker services run under the expected Trackly Compose project.
- Web container uses the trackly-job-applications-tracker-project-web prefix.
- PostgreSQL uses postgres:16-alpine.
- Django system check passes.
- Migrations are up to date.
- Sprint 3 Day 4 forms, services, selectors, views, URLs, templates, and tests exist.
- TargetRoleProfileForm normalises comma-separated keyword input.
- JobInsightGenerationForm limits target profile choices to the current user.
- Insight source text builders include the expected application and target profile fields.
- Source hashing changes when job text changes.
- generate_job_insight creates persisted insight output.
- Repeated service generation reuses unchanged insights.
- Service-level ownership checks reject cross-user applications.
- Service-level ownership checks reject cross-user target profiles.
- Browser target profile creation workflow works.
- Browser insight generation workflow works.
- Browser insight generation blocks another user's application.
- Application detail page renders insight generation UI.
- Application detail page renders the current compact latest insight summary.
- Admin login redirects to the admin dashboard.
- Playwright is installed and renders the admin dashboard with CSS grid layout.
- Sprint 3 Day 4 service tests pass.
- Sprint 3 Day 4 browser permission tests pass.
- Dashboard and auth regression tests pass.
- Full insights suite passes after Thursday workflow changes.
- Ruff and Black pass for Thursday Python files.
- Thursday templates and docs contain expected workflow/admin labels.
EOF
