#!/usr/bin/env bash
#
# Sprint 3 Day 3 console-only verification runbook for Trackly.
#
# Scope:
# Verify the implemented NLTK preprocessing and TF-IDF cosine similarity
# pipeline, including deterministic preprocessing, lemmatisation, similarity
# scoring, explainability terms, missing target terms, score labels, and the
# AI/NLP contract documentation.
#
# Expected Docker resources:
# - Compose project: trackly-job-applications-tracker-project
# - Web container prefix: trackly-job-applications-tracker-project-web
# - Database image: postgres:16-alpine
#
# Execution instructions:
# Run from the repository root, or from any directory:
#
#   chmod +x docs/sprint-runbook/sprint-3/sprint-3-day-3.sh
#   ./docs/sprint-runbook/sprint-3/sprint-3-day-3.sh
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


assert_file_contains() {
  local file_path="$1"
  local pattern="$2"
  local description="$3"

  if ! grep -qi "${pattern}" "${file_path}"; then
    printf "Expected %s to mention %s.\n" "${file_path}" "${description}" >&2
    exit 1
  fi

  printf "%s documents %s.\n" "${file_path}" "${description}"
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

print_header "Confirm Sprint 3 Day 3 files exist"

assert_file_exists "manage.py"
assert_file_exists "docker-compose.yml"
assert_file_exists "requirements.txt"
assert_file_exists "Dockerfile"
assert_file_exists "config/settings/base.py"
assert_file_exists "config/settings/local.py"
assert_file_exists "docs/ai-nlp-contract.md"

assert_directory_exists "apps/insights"
assert_directory_exists "apps/insights/nlp"
assert_file_exists "apps/insights/__init__.py"
assert_file_exists "apps/insights/apps.py"
assert_file_exists "apps/insights/models.py"
assert_file_exists "apps/insights/services.py"
assert_file_exists "apps/insights/migrations/0001_initial.py"
assert_file_exists "apps/insights/migrations/0002_jobinsight_weighted_evidence.py"
assert_file_exists "apps/insights/nlp/__init__.py"
assert_file_exists "apps/insights/nlp/text_processing.py"
assert_file_exists "apps/insights/nlp/similarity.py"
assert_file_exists "apps/insights/tests/test_text_processing.py"
assert_file_exists "apps/insights/tests/test_tfidf_similarity.py"
assert_file_exists "apps/insights/tests/test_services.py"

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

print_header "Verify migrations are up to date"

run_command compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Apply migrations"

run_command compose exec -T "${WEB_SERVICE}" python manage.py migrate --noinput "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Verify Sprint 3 Day 3 NLP module imports"

run_manage_shell "
from apps.insights.nlp.text_processing import (
    ensure_nltk_data_available,
    fallback_lemmatise,
    normalise_token,
    preprocess_text,
    preprocess_tokens,
)
from apps.insights.nlp.similarity import (
    PIPELINE_VERSION,
    analyse_text_similarity,
    build_target_profile_text,
    score_label_for,
    target_terms_from_text,
)

print(PIPELINE_VERSION)
print(ensure_nltk_data_available.__name__)
print(fallback_lemmatise.__name__)
print(normalise_token.__name__)
print(preprocess_text.__name__)
print(preprocess_tokens.__name__)
print(analyse_text_similarity.__name__)
print(build_target_profile_text.__name__)
print(score_label_for.__name__)
print(target_terms_from_text.__name__)
"

print_header "Verify NLTK runtime data and scikit-learn dependencies import"

run_manage_shell "
import nltk
import sklearn
from apps.insights.nlp.text_processing import ensure_nltk_data_available
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ensure_nltk_data_available()

print(nltk.__name__)
print(sklearn.__name__)
print(TfidfVectorizer.__name__)
print(cosine_similarity.__name__)
"

print_header "Verify preprocessing removes low-value terms from Tuesday evidence"

run_manage_shell "
from apps.insights.nlp.text_processing import preprocess_tokens

source_text = '''
Smoke Backend Engineer at Trackly Labs.
Python Django REST API PostgreSQL Docker testing.
Prepare examples about APIs and target role using modern backend practices.
'''

tokens = preprocess_tokens(source_text)
blocked_terms = {'and', 'about', 'target', 'role', 'using'}
leaked_terms = sorted(blocked_terms.intersection(tokens))

print(tokens)
print(leaked_terms)

if leaked_terms:
    raise SystemExit(f'Low-value terms leaked into preprocessing output: {leaked_terms}')
"

print_header "Verify fallback lemmatisation handles common technical text forms"

run_manage_shell "
from apps.insights.nlp.text_processing import fallback_lemmatise

checks = {
    'testing': 'test',
    'tested': 'test',
    'applications': 'application',
    'services': 'service',
}

for source, expected in checks.items():
    actual = fallback_lemmatise(source)
    print(f'{source} -> {actual}')
    if actual != expected:
        raise SystemExit(f'Expected {source} to become {expected}, got {actual}')
"

print_header "Verify clean text output is stable"

run_manage_shell "
from apps.insights.nlp.text_processing import preprocess_text

first = preprocess_text('Building tested Django services and APIs.')
second = preprocess_text('Building tested Django services and APIs.')

print(first)
print(second)

if first != second:
    raise SystemExit('Preprocessing output is not stable for repeated input.')

if 'django' not in first:
    raise SystemExit('Expected django to appear in preprocessed text.')
"

print_header "Verify target profile document builder"

run_manage_shell "
from apps.insights.nlp.similarity import build_target_profile_text

target_text = build_target_profile_text(
    title='Graduate Backend Engineer',
    description='Python Django APIs PostgreSQL Docker testing',
    keywords=['python', 'django', 'api', 'postgresql', 'docker', 'testing'],
)

print(target_text)

for expected in ['Graduate Backend Engineer', 'Python Django APIs', 'postgresql', 'docker']:
    if expected not in target_text:
        raise SystemExit(f'Expected target profile text to include {expected}')
"

print_header "Verify related text scores higher than unrelated text"

run_manage_shell "
from apps.insights.nlp.similarity import analyse_text_similarity, build_target_profile_text

target_text = build_target_profile_text(
    title='Graduate Backend Engineer',
    description='Python Django APIs PostgreSQL Docker testing',
    keywords=['python', 'django', 'api', 'postgresql', 'docker', 'testing'],
)

related = analyse_text_similarity(
    job_text='Python Django REST API PostgreSQL Docker testing role',
    target_text=target_text,
)

unrelated = analyse_text_similarity(
    job_text='Graphic design illustration branding and photography',
    target_text=target_text,
)

print(f'related={related.similarity_score}')
print(f'unrelated={unrelated.similarity_score}')

if related.similarity_score <= unrelated.similarity_score:
    raise SystemExit('Expected related job text to score higher than unrelated job text.')
"

print_header "Verify overlap and missing terms are explainable"

run_manage_shell "
from apps.insights.nlp.similarity import analyse_text_similarity

result = analyse_text_similarity(
    job_text='Python Django testing',
    target_text='Python Django PostgreSQL Docker testing',
)

print(result.top_overlapping_terms)
print(result.missing_target_terms)
print(result.explanation)

for expected in ['python', 'django']:
    if expected not in result.top_overlapping_terms:
        raise SystemExit(f'Expected overlap term {expected} to appear.')

for expected in ['postgresql', 'docker']:
    if expected not in result.missing_target_terms:
        raise SystemExit(f'Expected missing target term {expected} to appear.')

if 'docker' not in result.explanation:
    raise SystemExit('Expected explanation to include missing term docker.')
"

print_header "Verify score labels"

run_manage_shell "
from apps.insights.nlp.similarity import score_label_for

checks = {
    0.80: 'Excellent match',
    0.50: 'Strong match',
    0.25: 'Partial match',
    0.10: 'Low match',
}

for score, expected in checks.items():
    actual = score_label_for(score)
    print(f'{score} -> {actual}')
    if actual != expected:
        raise SystemExit(f'Expected {score} to map to {expected}, got {actual}')
"

print_header "Verify similarity output is deterministic"

run_manage_shell "
from apps.insights.nlp.similarity import analyse_text_similarity

first = analyse_text_similarity(
    job_text='Python Django REST API testing',
    target_text='Python Django REST API PostgreSQL',
)

second = analyse_text_similarity(
    job_text='Python Django REST API testing',
    target_text='Python Django REST API PostgreSQL',
)

print(first)
print(second)

if first != second:
    raise SystemExit('Expected repeated TF-IDF analysis to produce identical output.')
"

print_header "Verify empty input returns a safe low-match result"

run_manage_shell "
from apps.insights.nlp.similarity import analyse_text_similarity

result = analyse_text_similarity(job_text='', target_text='Python Django API')

print(result.similarity_score)
print(result.score_label)
print(result.explanation)

if result.similarity_score != 0.0:
    raise SystemExit('Expected empty job text to score 0.0.')

if result.score_label != 'Low match':
    raise SystemExit('Expected empty job text to return Low match.')
"

print_header "Run Sprint 3 Day 3 preprocessing tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/insights/tests/test_text_processing.py -q

print_header "Run Sprint 3 Day 3 TF-IDF similarity tests"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/insights/tests/test_tfidf_similarity.py -q

print_header "Run Sprint 3 Day 3 insights NLP test subset"

run_command compose exec -T "${WEB_SERVICE}" pytest \
  apps/insights/tests/test_text_processing.py \
  apps/insights/tests/test_tfidf_similarity.py \
  -q

print_header "Run all insights tests after Sprint 3 Day 3 pipeline checks"

run_command compose exec -T "${WEB_SERVICE}" pytest apps/insights -q

print_header "Run focused style checks for NLP code and tests"

run_command compose exec -T "${WEB_SERVICE}" python -m ruff check \
  apps/insights/nlp \
  apps/insights/tests/test_text_processing.py \
  apps/insights/tests/test_tfidf_similarity.py

run_command compose exec -T "${WEB_SERVICE}" python -m black \
  apps/insights/nlp \
  apps/insights/tests/test_text_processing.py \
  apps/insights/tests/test_tfidf_similarity.py \
  --check

print_header "Verify AI/NLP contract documents the implemented pipeline"

assert_file_contains "docs/ai-nlp-contract.md" "nltk" "NLTK preprocessing"
assert_file_contains "docs/ai-nlp-contract.md" "tf-idf" "TF-IDF vectorisation"
assert_file_contains "docs/ai-nlp-contract.md" "cosine" "cosine similarity"
assert_file_contains "docs/ai-nlp-contract.md" "overlapping" "overlapping terms"
assert_file_contains "docs/ai-nlp-contract.md" "missing target" "missing target terms"

print_header "Run final Sprint 3 Day 3 verification receipt"

run_command compose exec -T "${WEB_SERVICE}" pytest \
  apps/insights/tests/test_text_processing.py \
  apps/insights/tests/test_tfidf_similarity.py \
  -q

run_command compose exec -T "${WEB_SERVICE}" pytest apps/insights -q

run_command compose exec -T "${WEB_SERVICE}" python manage.py check "--settings=${DJANGO_SETTINGS_MODULE}"

run_command compose exec -T "${WEB_SERVICE}" python manage.py makemigrations --check --dry-run "--settings=${DJANGO_SETTINGS_MODULE}"

print_header "Sprint 3 Day 3 verification complete"

cat <<'EOF'
Completion checkpoint:
- Docker services run under the expected Trackly Compose project.
- Web container uses the trackly-job-applications-tracker-project-web prefix.
- PostgreSQL uses postgres:16-alpine.
- Django system check passes.
- Migrations are up to date.
- NLTK runtime data is available.
- scikit-learn imports correctly.
- Sprint 3 Day 3 NLP modules import correctly.
- Preprocessing output is stable.
- Low-value terms from Tuesday evidence are filtered.
- Fallback lemmatisation handles common technical text forms.
- Target profile text is built from title, description, and keywords.
- Related job text scores higher than unrelated job text.
- Overlapping high-value terms are extracted.
- Missing target terms are extracted.
- Score labels map to expected thresholds.
- Empty inputs return a safe Low match result.
- TF-IDF similarity output is deterministic for fixed inputs.
- Sprint 3 Day 3 preprocessing tests pass.
- Sprint 3 Day 3 TF-IDF similarity tests pass.
- Full insights test suite passes after Sprint 3 Day 3 pipeline checks.
- Ruff and Black pass for NLP code and tests.
- docs/ai-nlp-contract.md documents NLTK, TF-IDF, cosine similarity, overlapping terms, and missing target terms.
EOF
