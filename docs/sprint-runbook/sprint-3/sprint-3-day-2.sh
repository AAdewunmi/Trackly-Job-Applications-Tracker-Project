#!/usr/bin/env bash
#
# Sprint 3 Day 2 console-only verification runbook for Trackly.
#
# Scope:
# Verify the insights app persistence boundary, TargetRoleProfile, JobInsight,
# admin registration, factories, model/service tests, migration state, TF-IDF
# pipeline contract enforcement, and retrieval-style insight persistence fields.
#
# Expected Docker resources:
# - Compose project: trackly-job-applications-tracker-project
# - Web container prefix: trackly-job-applications-tracker-project-web
# - Database image: postgres:16-alpine
#
# Execution instructions:
# Run from the repository root, or from any directory:
#
#   chmod +x docs/sprint-runbook/sprint-3/sprint-3-day-2.sh
#   ./docs/sprint-runbook/sprint-3/sprint-3-day-2.sh
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
INSIGHTS_SMOKE_EMAIL="${INSIGHTS_SMOKE_EMAIL:-insights.smoke@example.com}"
INSIGHTS_SMOKE_PASSWORD="${INSIGHTS_SMOKE_PASSWORD:-SmokePass12345}"

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


run_manage_shell() {
  local code="$1"

  print_command compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "<python>"
  compose exec -T "${WEB_SERVICE}" python manage.py shell "--settings=${DJANGO_SETTINGS_MODULE}" -c "${code}"
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

print_header "Confirm Sprint 3 Day 2 files exist"

assert_file_exists "manage.py"
assert_file_exists "docker-compose.yml"
assert_file_exists "requirements.txt"
assert_file_exists "config/settings/base.py"
assert_file_exists "config/settings/local.py"
assert_file_exists "docs/ai-nlp-contract.md"

assert_directory_exists "apps/insights"
assert_file_exists "apps/insights/__init__.py"
assert_file_exists "apps/insights/apps.py"
assert_file_exists "apps/insights/models.py"
assert_file_exists "apps/insights/admin.py"
assert_file_exists "apps/insights/factories.py"
assert_file_exists "apps/insights/services.py"
assert_file_exists "apps/insights/migrations/0001_initial.py"
assert_file_exists "apps/insights/tests/__init__.py"
assert_file_exists "apps/insights/tests/test_models.py"
assert_file_exists "apps/insights/tests/test_services.py"

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

print_header "Verify apps.insights is installed"

run_manage_shell "
from django.conf import settings

installed = 'apps.insights' in settings.INSTALLED_APPS
print(installed)
if not installed:
    raise SystemExit('apps.insights is not installed.')
"

print_header "Verify insights app, models, admin, factories, and service import"

run_manage_shell "
import apps.insights.admin

from apps.insights.apps import InsightsConfig
from apps.insights.factories import JobInsightFactory, TargetRoleProfileFactory
from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.services import generate_job_insight

print(InsightsConfig.name)
print(TargetRoleProfile.__name__)
print(JobInsight.__name__)
print(TargetRoleProfileFactory.__name__)
print(JobInsightFactory.__name__)
print(generate_job_insight.__name__)
print('insights admin imported')
"

print_header "Verify migrations are up to date"

run_command compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Apply migrations"

run_command compose exec -T "${WEB_SERVICE}" python manage.py migrate --noinput "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Confirm insights migration state"

run_command compose exec -T "${WEB_SERVICE}" python manage.py showmigrations insights "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Confirm insights database tables exist"

run_manage_shell "
from django.db import connection

tables = connection.introspection.table_names()
expected_tables = {'insights_targetroleprofile', 'insights_jobinsight'}
missing_tables = sorted(expected_tables - set(tables))

print('insights_targetroleprofile' in tables)
print('insights_jobinsight' in tables)

if missing_tables:
    raise SystemExit(f'Missing insights tables: {missing_tables}')
"

print_header "Verify TF-IDF pipeline contract"

run_manage_shell "
from django.core.exceptions import ValidationError

from apps.insights.models import JobInsight
from apps.insights.services import PIPELINE_VERSION

expected = JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1
print(expected)
print(PIPELINE_VERSION)

if PIPELINE_VERSION != expected:
    raise SystemExit(f'Expected service pipeline {expected}, got {PIPELINE_VERSION}')

field = JobInsight._meta.get_field('pipeline_version')
allowed_values = {choice[0] for choice in field.choices}
print(sorted(allowed_values))

if allowed_values != {expected}:
    raise SystemExit(f'Expected only {expected} pipeline choice, got {allowed_values}')

insight = JobInsight(pipeline_version='embedding-cosine-v1')
try:
    insight.full_clean(exclude=['job_application', 'target_profile', 'source_hash', 'similarity_score', 'score_label', 'explanation'])
except ValidationError:
    print(True)
else:
    raise SystemExit('Unsupported pipeline version should fail validation.')
"

print_header "Run Sprint 3 Day 2 insights tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/insights -q

print_header "Run focused style checks for insights code and tests"

run_command compose exec -T "${WEB_SERVICE}" python -m ruff check apps/insights
run_command compose exec -T "${WEB_SERVICE}" python -m black apps/insights --check

print_header "Create console smoke-test user"

run_manage_shell "
from django.contrib.auth import get_user_model

User = get_user_model()
User.objects.filter(email='${INSIGHTS_SMOKE_EMAIL}').delete()
User.objects.create_user(
    email='${INSIGHTS_SMOKE_EMAIL}',
    password='${INSIGHTS_SMOKE_PASSWORD}',
    first_name='Insights',
    last_name='Smoke',
)
print('created')
"

print_header "Create smoke-test job application"

run_manage_shell "
from django.contrib.auth import get_user_model

from apps.jobs.models import JobApplication

User = get_user_model()
user = User.objects.get(email='${INSIGHTS_SMOKE_EMAIL}')
JobApplication.objects.filter(owner=user, title='Smoke Backend Engineer').delete()
application = JobApplication.objects.create(
    owner=user,
    title='Smoke Backend Engineer',
    company='Trackly Labs',
    status=JobApplication.Status.APPLIED,
    job_description='Python Django REST API PostgreSQL Docker testing.',
    notes='Prepare examples about APIs and testing.',
)
print(application.id)
"

print_header "Create smoke-test target role profile"

run_manage_shell "
from django.contrib.auth import get_user_model

from apps.insights.models import TargetRoleProfile

User = get_user_model()
user = User.objects.get(email='${INSIGHTS_SMOKE_EMAIL}')
TargetRoleProfile.objects.filter(owner=user, title='Smoke Backend Target').delete()
profile = TargetRoleProfile.objects.create(
    owner=user,
    title='Smoke Backend Target',
    description='Backend role using Python and Django.',
    keywords=['Python', 'Django', 'API', 'PostgreSQL', 'Docker', 'Testing'],
)
print(profile.id)
print(profile.keywords)

if profile.keywords != ['python', 'django', 'api', 'postgresql', 'docker', 'testing']:
    raise SystemExit(f'Unexpected normalised keywords: {profile.keywords}')
"

print_header "Generate smoke-test job insight through the service"

run_manage_shell "
from django.contrib.auth import get_user_model

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.services import generate_job_insight
from apps.jobs.models import JobApplication

User = get_user_model()
user = User.objects.get(email='${INSIGHTS_SMOKE_EMAIL}')
application = JobApplication.objects.get(owner=user, title='Smoke Backend Engineer')
profile = TargetRoleProfile.objects.get(owner=user, title='Smoke Backend Target')
JobInsight.objects.filter(job_application=application, target_profile=profile).delete()
insight = generate_job_insight(application, target_profile=profile)

print(insight.id)
print(insight.score_label)
print(insight.pipeline_version)
print(insight.similarity_score)
print(insight.extracted_terms)
print(insight.top_overlapping_terms)
print(insight.missing_target_terms)

if insight.pipeline_version != JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1:
    raise SystemExit(f'Unexpected pipeline version: {insight.pipeline_version}')
if not insight.extracted_terms:
    raise SystemExit('Expected extracted terms.')
"

print_header "Verify repeated generation reuses unchanged insight"

run_manage_shell "
from django.contrib.auth import get_user_model

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.services import generate_job_insight
from apps.jobs.models import JobApplication

User = get_user_model()
user = User.objects.get(email='${INSIGHTS_SMOKE_EMAIL}')
application = JobApplication.objects.get(owner=user, title='Smoke Backend Engineer')
profile = TargetRoleProfile.objects.get(owner=user, title='Smoke Backend Target')

first = generate_job_insight(application, target_profile=profile)
second = generate_job_insight(application, target_profile=profile)
count = JobInsight.objects.filter(
    job_application=application,
    target_profile=profile,
    source_hash=first.source_hash,
    pipeline_version=first.pipeline_version,
).count()

print(first.id)
print(second.id)
print(count)

if first.id != second.id:
    raise SystemExit('Expected unchanged insight generation to reuse the same record.')
if count != 1:
    raise SystemExit(f'Expected one unchanged insight record, got {count}.')
"

print_header "Verify ownership validation rejects mismatched insight ownership"

run_manage_shell "
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import JobApplication

User = get_user_model()
User.objects.filter(email='insights.other@example.com').delete()
other = User.objects.create_user(email='insights.other@example.com', password='${INSIGHTS_SMOKE_PASSWORD}')
application = JobApplication.objects.get(owner__email='${INSIGHTS_SMOKE_EMAIL}', title='Smoke Backend Engineer')
profile = TargetRoleProfile.objects.create(
    owner=other,
    title='Other Target',
    description='Other target.',
    keywords=['python'],
)
insight = JobInsight(
    job_application=application,
    target_profile=profile,
    source_hash='b' * 64,
    pipeline_version=JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1,
    clean_job_text='python',
    clean_target_text='python',
    extracted_terms=['python'],
    top_overlapping_terms=['python'],
    missing_target_terms=[],
    similarity_score=1.0,
    score_label='Strong match',
    explanation='Strong match.',
)

try:
    insight.full_clean()
except ValidationError:
    print(True)
else:
    raise SystemExit('Expected mismatched insight ownership validation to fail.')
"

print_header "Verify JSON list validation rejects invalid insight fields"

run_manage_shell "
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import JobApplication

User = get_user_model()
user = User.objects.get(email='${INSIGHTS_SMOKE_EMAIL}')
application = JobApplication.objects.get(owner=user, title='Smoke Backend Engineer')
profile = TargetRoleProfile.objects.get(owner=user, title='Smoke Backend Target')
insight = JobInsight(
    job_application=application,
    target_profile=profile,
    source_hash='c' * 64,
    pipeline_version=JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1,
    clean_job_text='python',
    clean_target_text='python',
    extracted_terms='python',
    top_overlapping_terms=['python'],
    missing_target_terms=[],
    similarity_score=1.0,
    score_label='Strong match',
    explanation='Strong match.',
)

try:
    insight.full_clean()
except ValidationError:
    print(True)
else:
    raise SystemExit('Expected non-list insight terms validation to fail.')
"

print_header "Verify duplicate unchanged insights are blocked"

run_manage_shell "
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import JobApplication

User = get_user_model()
user = User.objects.get(email='${INSIGHTS_SMOKE_EMAIL}')
application = JobApplication.objects.get(owner=user, title='Smoke Backend Engineer')
profile = TargetRoleProfile.objects.get(owner=user, title='Smoke Backend Target')
JobInsight.objects.filter(
    job_application=application,
    target_profile=profile,
    source_hash='d' * 64,
    pipeline_version=JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1,
).delete()

payload = {
    'job_application': application,
    'target_profile': profile,
    'source_hash': 'd' * 64,
    'pipeline_version': JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1,
    'clean_job_text': 'python',
    'clean_target_text': 'python',
    'extracted_terms': ['python'],
    'top_overlapping_terms': ['python'],
    'missing_target_terms': [],
    'similarity_score': 1.0,
    'score_label': 'Strong match',
    'explanation': 'Strong match.',
}
JobInsight.objects.create(**payload)

try:
    JobInsight.objects.create(**payload)
except (ValidationError, IntegrityError):
    print(True)
else:
    raise SystemExit('Expected duplicate unchanged insight creation to fail.')
"

print_header "Verify AI/NLP contract document"

run_command grep -i "retrieval-style" docs/ai-nlp-contract.md
run_command grep -i "nltk-tfidf-cosine-v1" docs/ai-nlp-contract.md
run_command grep -i "tf-idf" docs/ai-nlp-contract.md
run_command grep -i "cosine" docs/ai-nlp-contract.md

print_header "Run final Sprint 3 Day 2 verification receipt"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/insights -q
run_command compose exec -T "${WEB_SERVICE}" python manage.py check "--settings=${DJANGO_SETTINGS_MODULE}"
run_command compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Sprint 3 Day 2 verification complete"

cat <<'EOF'
Completion checkpoint:
- apps.insights is installed.
- TargetRoleProfile imports correctly.
- JobInsight imports correctly.
- Insight admin registrations import correctly.
- Insight factories and services import correctly.
- Insight migrations exist and are applied.
- insights_targetroleprofile exists in PostgreSQL.
- insights_jobinsight exists in PostgreSQL.
- Target profile keywords are normalised to lowercase.
- Job insights persist retrieval-style output fields.
- TF-IDF pipeline version is enforced.
- Unsupported non-TF-IDF pipeline versions are rejected.
- Ownership validation blocks mismatched application/profile owners.
- JSON list validation works.
- Duplicate unchanged insights are blocked.
- Repeated service generation reuses unchanged insight records.
- docs/ai-nlp-contract.md documents the retrieval-style NLP contract.
- Sprint 3 Day 2 insights tests pass.
EOF
