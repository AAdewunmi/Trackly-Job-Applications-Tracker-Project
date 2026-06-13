#!/usr/bin/env bash

# Sprint 3 Day 5 console-only verification runbook.
#
# Execution:
#   chmod +x docs/sprint-runbook/sprint-3/sprint-3-day-5.sh
#   ./docs/sprint-runbook/sprint-3/sprint-3-day-5.sh
#
# This runbook verifies the Friday insights dashboard/API work against the
# current Trackly project structure. It intentionally uses the Docker Compose
# project name that produces the expected web container prefix:
#   trackly-job-applications-tracker-project-web
# and verifies PostgreSQL runs from:
#   postgres:16-alpine

set -Eeuo pipefail

PROJECT_ROOT="/Users/adrianadewunmi/VSCODE/Trackly-Job-Applications-Tracker-Project"
COMPOSE_PROJECT_NAME="trackly-job-applications-tracker-project"
EXPECTED_WEB_CONTAINER_PREFIX="trackly-job-applications-tracker-project-web"
EXPECTED_DB_IMAGE="postgres:16-alpine"
WEB_SERVICE="web"
DB_SERVICE="db"
DJANGO_SETTINGS_MODULE="config.settings.local"
DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0,testserver"

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
  printf "$ compose exec -T -e DJANGO_SETTINGS_MODULE=%s -e DJANGO_ALLOWED_HOSTS=%s %s python - <python>\n" "${DJANGO_SETTINGS_MODULE}" "${DJANGO_ALLOWED_HOSTS}" "${WEB_SERVICE}"
  compose exec -T \
    -e DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
    -e DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS}" \
    "${WEB_SERVICE}" python -
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

section "Confirm Sprint 3 Day 5 files exist"
assert_file_exists "apps/insights/api/__init__.py"
assert_file_exists "apps/insights/api/serializers.py"
assert_file_exists "apps/insights/api/views.py"
assert_file_exists "apps/insights/api/urls.py"
assert_file_exists "apps/insights/tests/api/test_insight_api.py"
assert_file_exists "apps/insights/tests/test_views.py"
assert_file_exists "apps/insights/views.py"
assert_file_exists "apps/insights/selectors.py"
assert_file_exists "templates/insights/insight_list.html"
assert_file_exists "templates/base.html"
assert_file_exists "docs/api-contract.md"
assert_file_exists "docs/ai-nlp-contract.md"
assert_file_exists "README.md"

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
WEB_CONTAINER_ID="$(compose ps -q "${WEB_SERVICE}")"
WEB_CONTAINER_NAME="$(docker inspect --format '{{ .Name }}' "${WEB_CONTAINER_ID}" | sed 's#^/##')"
printf "WEB_CONTAINER_NAME=%s\n" "${WEB_CONTAINER_NAME}"

if [[ "${WEB_CONTAINER_NAME}" != "${EXPECTED_WEB_CONTAINER_PREFIX}"* ]]; then
  printf "Expected web container name to start with %s, got %s\n" "${EXPECTED_WEB_CONTAINER_PREFIX}" "${WEB_CONTAINER_NAME}" >&2
  exit 1
fi

section "Confirm PostgreSQL image"
DB_CONTAINER_ID="$(compose ps -q "${DB_SERVICE}")"
DB_IMAGE="$(docker inspect --format '{{ .Config.Image }}' "${DB_CONTAINER_ID}")"
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

section "Verify Sprint 3 Day 5 imports"
django_python <<'PY'
import django

django.setup()

from apps.insights.api.serializers import GenerateJobInsightSerializer, JobInsightSerializer
from apps.insights.api.views import GenerateJobInsightAPIView, JobInsightListAPIView
from apps.insights.selectors import get_insights_for_user, get_recent_insights_for_user
from apps.insights.views import DashboardGenerateJobInsightView, InsightListView

print(JobInsightSerializer.__name__)
print(GenerateJobInsightSerializer.__name__)
print(JobInsightListAPIView.__name__)
print(GenerateJobInsightAPIView.__name__)
print(get_insights_for_user.__name__)
print(get_recent_insights_for_user.__name__)
print(InsightListView.__name__)
print(DashboardGenerateJobInsightView.__name__)
PY

section "Verify Sprint 3 Day 5 browser and API URL paths"
django_python <<'PY'
import django

django.setup()

from django.urls import NoReverseMatch, reverse


def reverse_first(names):
    for name in names:
        try:
            return name, reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


checks = [
    (["insights:insight-list"], "/insights/"),
    (["insights:dashboard-job-insight-generate"], "/insights/generate/"),
    (["insights_api:job-insight-list", "job-insight-list"], "/api/v1/insights/"),
    (
        ["insights_api:job-insight-generate", "job-insight-generate"],
        "/api/v1/insights/generate/",
    ),
]

for names, expected_path in checks:
    name, actual_path = reverse_first(names)
    print(f"{name} -> {actual_path}")

    if actual_path != expected_path:
        raise SystemExit(f"Expected {name} to resolve to {expected_path}, got {actual_path}")
PY

section "Verify insight dashboard requires login"
django_python <<'PY'
import django

django.setup()

from django.test import Client
from django.urls import reverse

client = Client()
response = client.get(reverse("insights:insight-list"))

print(response.status_code)
print(response.url)

if response.status_code != 302:
    raise SystemExit("Expected anonymous insights dashboard access to redirect.")

if "/login" not in response.url:
    raise SystemExit("Expected anonymous dashboard access to redirect to login.")
PY

section "Verify insight dashboard renders setup empty state"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()
User.objects.filter(email="day5.empty@example.com").delete()
user = User.objects.create_user(
    email="day5.empty@example.com",
    password="SmokePass12345",
)

client = Client()
client.force_login(user)

response = client.get(reverse("insights:insight-list"))
content = response.content.decode("utf-8")

print(response.status_code)

if response.status_code != 200:
    raise SystemExit("Expected insights dashboard to render for authenticated user.")

for expected in [
    "Set up retrieval-style insights",
    "Add an application before generating dashboard insights.",
    "Create an active target role profile before generating dashboard insights.",
]:
    if expected not in content:
        raise SystemExit(f"Expected insights dashboard setup empty state to contain {expected}")
PY

section "Verify insight dashboard renders no-insights empty state"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.insights.factories import TargetRoleProfileFactory

User = get_user_model()
User.objects.filter(email="day5.noinsights@example.com").delete()
user = User.objects.create_user(
    email="day5.noinsights@example.com",
    password="SmokePass12345",
)
TargetRoleProfileFactory(owner=user, title="Empty Target")

client = Client()
client.force_login(user)

response = client.get(reverse("insights:insight-list"))
content = response.content.decode("utf-8")

print(response.status_code)

if response.status_code != 200:
    raise SystemExit("Expected insights dashboard to render for authenticated user.")

if "No job insights yet" not in content:
    raise SystemExit("Expected no-insights empty state when a target profile exists.")
PY

section "Verify insight dashboard renders recent insights"
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
User.objects.filter(email="day5.dashboard@example.com").delete()
user = User.objects.create_user(
    email="day5.dashboard@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    title="Dashboard Django Engineer",
    company="Trackly Labs",
    job_description="Python Django REST API PostgreSQL Docker testing.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    title="Dashboard Backend Target",
    keywords=["python", "django", "api", "postgresql", "docker", "testing"],
)

generate_job_insight(
    user=user,
    application=application,
    target_profile=profile,
)

client = Client()
client.force_login(user)

response = client.get(reverse("insights:insight-list"))
content = response.content.decode("utf-8")

print(response.status_code)

for expected in [
    "Job-fit insights",
    "Dashboard Django Engineer",
    "Dashboard Backend Target",
    "Extracted",
    "Overlap",
    "Missing",
]:
    if expected not in content:
        raise SystemExit(f"Expected insights dashboard to contain {expected}")

if response.status_code != 200:
    raise SystemExit("Expected insights dashboard to render successfully.")
PY

section "Verify dashboard does not leak another user's insights"
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
User.objects.filter(email__in=["day5.owner@example.com", "day5.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day5.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day5.other@example.com",
    password="SmokePass12345",
)

owner_application = JobApplicationFactory(
    owner=owner,
    title="Owner Visible Role",
    job_description="Python Django API testing.",
)
owner_profile = TargetRoleProfileFactory(owner=owner, title="Owner Target")
generate_job_insight(
    user=owner,
    application=owner_application,
    target_profile=owner_profile,
)

other_application = JobApplicationFactory(
    owner=other,
    title="Other Hidden Role",
    job_description="React design branding.",
)
other_profile = TargetRoleProfileFactory(owner=other, title="Other Target")
generate_job_insight(
    user=other,
    application=other_application,
    target_profile=other_profile,
)

client = Client()
client.force_login(owner)

response = client.get(reverse("insights:insight-list"))
content = response.content.decode("utf-8")

print(response.status_code)

if "Owner Visible Role" not in content:
    raise SystemExit("Expected owner insight to render.")

if "Other Hidden Role" in content:
    raise SystemExit("Expected another user's insight to be hidden.")
PY

section "Verify unauthenticated insights API list is rejected"
django_python <<'PY'
import django

django.setup()

from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient


def reverse_first(names):
    for name in names:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


url = reverse_first(["insights_api:job-insight-list", "job-insight-list"])
response = APIClient().get(url)

print(response.status_code)

if response.status_code != status.HTTP_401_UNAUTHORIZED:
    raise SystemExit("Expected unauthenticated insight API list to return 401.")
PY

section "Verify authenticated insights API list returns only current user's insights"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email__in=["day5.api.owner@example.com", "day5.api.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day5.api.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day5.api.other@example.com",
    password="SmokePass12345",
)

owner_application = JobApplicationFactory(
    owner=owner,
    title="API Owner Role",
    job_description="Python Django PostgreSQL Docker.",
)
owner_profile = TargetRoleProfileFactory(owner=owner, title="API Owner Target")
owner_result = generate_job_insight(
    user=owner,
    application=owner_application,
    target_profile=owner_profile,
)

other_application = JobApplicationFactory(
    owner=other,
    title="API Other Role",
    job_description="Graphic design branding.",
)
other_profile = TargetRoleProfileFactory(owner=other, title="API Other Target")
generate_job_insight(
    user=other,
    application=other_application,
    target_profile=other_profile,
)


def reverse_first(names):
    for name in names:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


client = APIClient()
client.force_authenticate(user=owner)

response = client.get(reverse_first(["insights_api:job-insight-list", "job-insight-list"]))

print(response.status_code)
print(response.data)

if response.status_code != status.HTTP_200_OK:
    raise SystemExit("Expected authenticated insight list to return 200.")

ids = [item["id"] for item in response.data]

if owner_result.insight.id not in ids:
    raise SystemExit("Expected current user's insight in API list.")

if len(ids) != 1:
    raise SystemExit("Expected API list to include only current user's insights.")
PY

section "Verify authenticated insights API generation creates insight"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day5.api.generate@example.com").delete()

user = User.objects.create_user(
    email="day5.api.generate@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    title="API Generated Django Role",
    job_description="Python Django REST API PostgreSQL Docker testing.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    title="API Backend Target",
    keywords=["python", "django", "api", "postgresql", "docker", "testing"],
)


def reverse_first(names):
    for name in names:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


client = APIClient()
client.force_authenticate(user=user)

response = client.post(
    reverse_first(["insights_api:job-insight-generate", "job-insight-generate"]),
    {
        "job_application_id": application.id,
        "target_profile_id": profile.id,
    },
    format="json",
)

print(response.status_code)
print(response.data)

if response.status_code != status.HTTP_201_CREATED:
    raise SystemExit("Expected first API insight generation to return 201.")

if response.data["created"] is not True:
    raise SystemExit("Expected first API generation response to mark created true.")

if not JobInsight.objects.filter(job_application=application, target_profile=profile).exists():
    raise SystemExit("Expected API insight generation to persist JobInsight.")
PY

section "Verify repeated API generation reuses unchanged insight"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.models import JobInsight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day5.api.idempotent@example.com").delete()

user = User.objects.create_user(
    email="day5.api.idempotent@example.com",
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


def reverse_first(names):
    for name in names:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


client = APIClient()
client.force_authenticate(user=user)
url = reverse_first(["insights_api:job-insight-generate", "job-insight-generate"])
payload = {
    "job_application_id": application.id,
    "target_profile_id": profile.id,
}

first = client.post(url, payload, format="json")
second = client.post(url, payload, format="json")

print(first.status_code)
print(second.status_code)
print(first.data)
print(second.data)
print(JobInsight.objects.filter(job_application=application, target_profile=profile).count())

if first.status_code != status.HTTP_201_CREATED:
    raise SystemExit("Expected first API generation to return 201.")

if second.status_code != status.HTTP_200_OK:
    raise SystemExit("Expected repeated API generation to return 200.")

if second.data["created"] is not False:
    raise SystemExit("Expected repeated API generation to mark created false.")

if JobInsight.objects.filter(job_application=application, target_profile=profile).count() != 1:
    raise SystemExit("Expected repeated API generation to reuse unchanged insight.")
PY

section "Verify insights API blocks another user's application"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.insights.factories import TargetRoleProfileFactory
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email__in=["day5.api.app.owner@example.com", "day5.api.app.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day5.api.app.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day5.api.app.other@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(owner=owner)
profile = TargetRoleProfileFactory(owner=other)


def reverse_first(names):
    for name in names:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


client = APIClient()
client.force_authenticate(user=other)

response = client.post(
    reverse_first(["insights_api:job-insight-generate", "job-insight-generate"]),
    {
        "job_application_id": application.id,
        "target_profile_id": profile.id,
    },
    format="json",
)

print(response.status_code)

if response.status_code != status.HTTP_404_NOT_FOUND:
    raise SystemExit("Expected API to hide another user's application with 404.")
PY

section "Verify insights API blocks another user's target profile"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.insights.factories import TargetRoleProfileFactory
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email__in=["day5.api.profile.owner@example.com", "day5.api.profile.other@example.com"]).delete()

owner = User.objects.create_user(
    email="day5.api.profile.owner@example.com",
    password="SmokePass12345",
)
other = User.objects.create_user(
    email="day5.api.profile.other@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(owner=owner)
profile = TargetRoleProfileFactory(owner=other)


def reverse_first(names):
    for name in names:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue

    raise SystemExit(f"None of these URL names resolved: {names}")


client = APIClient()
client.force_authenticate(user=owner)

response = client.post(
    reverse_first(["insights_api:job-insight-generate", "job-insight-generate"]),
    {
        "job_application_id": application.id,
        "target_profile_id": profile.id,
    },
    format="json",
)

print(response.status_code)

if response.status_code != status.HTTP_404_NOT_FOUND:
    raise SystemExit("Expected API to hide another user's target profile with 404.")
PY

section "Verify insight API serializer output shape"
django_python <<'PY'
import django

django.setup()

from django.contrib.auth import get_user_model

from apps.insights.api.serializers import JobInsightSerializer
from apps.insights.factories import TargetRoleProfileFactory
from apps.insights.services import generate_job_insight
from apps.jobs.factories import JobApplicationFactory

User = get_user_model()
User.objects.filter(email="day5.serializer@example.com").delete()

user = User.objects.create_user(
    email="day5.serializer@example.com",
    password="SmokePass12345",
)

application = JobApplicationFactory(
    owner=user,
    title="Serializer Django Role",
    job_description="Python Django REST API PostgreSQL Docker testing.",
)
profile = TargetRoleProfileFactory(
    owner=user,
    title="Serializer Backend Target",
    keywords=["python", "django", "api", "postgresql", "docker", "testing"],
)
result = generate_job_insight(
    user=user,
    application=application,
    target_profile=profile,
)

data = JobInsightSerializer(result.insight).data

print(data)

expected_fields = {
    "id",
    "job_application",
    "job_application_title",
    "target_profile",
    "target_profile_title",
    "source_hash",
    "pipeline_version",
    "extracted_terms",
    "top_overlapping_terms",
    "top_overlapping_weighted_terms",
    "missing_target_terms",
    "missing_weighted_target_terms",
    "similarity_score",
    "score_label",
    "explanation",
    "created_at",
}

missing_fields = sorted(expected_fields.difference(data.keys()))

if missing_fields:
    raise SystemExit(f"Serializer missing fields: {missing_fields}")

if data["job_application_title"] != "Serializer Django Role":
    raise SystemExit("Expected serializer to include job application title.")

if data["target_profile_title"] != "Serializer Backend Target":
    raise SystemExit("Expected serializer to include target profile title.")

if not data["top_overlapping_weighted_terms"]:
    raise SystemExit("Expected serializer to include weighted overlap evidence.")
PY

section "Run Sprint 3 Day 5 dashboard tests"
run_compose exec -T "${WEB_SERVICE}" pytest apps/insights/tests/test_views.py -q

section "Run Sprint 3 Day 5 insight API tests"
run_compose exec -T "${WEB_SERVICE}" pytest apps/insights/tests/api/test_insight_api.py -q

section "Run Sprint 3 Day 5 test subset"
run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/insights/tests/test_views.py \
  apps/insights/tests/api/test_insight_api.py \
  -q

section "Run Sprint 3 API and insights regression tests"
run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/jobs/tests/api \
  apps/insights \
  -q

section "Run full project test suite"
run_compose exec -T "${WEB_SERVICE}" pytest -q

section "Run focused style checks for Friday Python files"
run_compose exec -T "${WEB_SERVICE}" python -m ruff check \
  apps/insights/api \
  apps/insights/tests/api/test_insight_api.py \
  apps/insights/tests/test_views.py \
  apps/insights/views.py \
  apps/insights/selectors.py

run_compose exec -T "${WEB_SERVICE}" python -m black \
  apps/insights/api \
  apps/insights/tests/api/test_insight_api.py \
  apps/insights/tests/test_views.py \
  apps/insights/views.py \
  apps/insights/selectors.py \
  --check

section "Verify templates and docs contain Friday feature labels"
run grep -i "Job-fit insights" templates/insights/insight_list.html
run grep -i "Target role profiles" templates/insights/insight_list.html
run grep -i "Overlap" templates/insights/insight_list.html
run grep -i "Missing" templates/insights/insight_list.html
run grep -i "/api/v1/insights" docs/api-contract.md
run grep -i "generate" docs/api-contract.md
run grep -i "retrieval-style" README.md
run grep -i "TF-IDF" README.md
run grep -i "cosine" README.md

section "Run final Sprint 3 Day 5 verification receipt"
run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/insights/tests/test_views.py \
  apps/insights/tests/api/test_insight_api.py \
  -q

run_compose exec -T "${WEB_SERVICE}" pytest \
  apps/jobs/tests/api \
  apps/insights \
  -q

run_compose exec -T "${WEB_SERVICE}" python manage.py check --settings="${DJANGO_SETTINGS_MODULE}"

run_compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run --settings="${DJANGO_SETTINGS_MODULE}"

section "Sprint 3 Day 5 verification complete"
cat <<'EOF'
Completion checkpoint:
- Docker services run under the expected Trackly Compose project.
- Web container uses the trackly-job-applications-tracker-project-web prefix.
- PostgreSQL uses postgres:16-alpine.
- Django system check passes.
- Migrations are up to date.
- Sprint 3 Day 5 insights API files, dashboard tests, templates, docs, and README exist.
- Insights dashboard requires login.
- Insights dashboard renders setup and no-insights empty states.
- Insights dashboard renders recent stored insights.
- Insights dashboard does not leak another user's insights.
- Unauthenticated insight API list access returns 401.
- Authenticated insight API list returns only the current user's insights.
- Authenticated insight API generation creates a stored insight.
- Repeated insight API generation reuses unchanged insight records.
- Insight API blocks another user's application.
- Insight API blocks another user's target profile.
- Insight API serializer exposes filtered terms and weighted evidence fields.
- Sprint 3 Day 5 dashboard tests pass.
- Sprint 3 Day 5 insight API tests pass.
- Sprint 3 API and insights regression tests pass.
- Full project test suite passes.
- Ruff and Black pass for Friday Python files.
- Templates and docs contain expected Friday feature labels.
EOF
