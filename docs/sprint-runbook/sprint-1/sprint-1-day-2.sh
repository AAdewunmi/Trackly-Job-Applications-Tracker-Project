#!/usr/bin/env bash
set -euo pipefail

# Sprint 1 Day 2 console-only verification runbook.
#
# Purpose:
#   Verify the PostgreSQL-backed local Docker baseline for Trackly.
#
# Run from the repository root:
#   chmod +x docs/sprint-runbook/sprint-1/sprint-1-day-2.sh
#   ./docs/sprint-runbook/sprint-1/sprint-1-day-2.sh
#
# Expected final receipt:
#   System check identified no issues (0 silenced).
#   Sprint 1 Day 2 PostgreSQL baseline verified
#
# Notes:
#   Docker Compose automatically reads .env when present. This runbook verifies
#   the local Docker baseline, so it exports known local values before Compose
#   runs. That prevents production-shaped .env values from changing the test.
#   Use SPRINT1_DAY2_* variables only if this runbook needs custom values.
#   It also uses a dedicated Compose project name to avoid reusing an existing
#   local database volume that may have been initialized with different values.
#
# Optional cleanup after verification:
#   docker compose -p trackly_sprint1_day2 down

export DJANGO_SECRET_KEY="${SPRINT1_DAY2_DJANGO_SECRET_KEY:-sprint-1-day-2-local-secret-key}"
export DJANGO_DEBUG="${SPRINT1_DAY2_DJANGO_DEBUG:-True}"
export DJANGO_ALLOWED_HOSTS="${SPRINT1_DAY2_DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,0.0.0.0}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${SPRINT1_DAY2_DJANGO_CSRF_TRUSTED_ORIGINS:-http://localhost:8000,http://127.0.0.1:8000}"
export POSTGRES_DB="${SPRINT1_DAY2_POSTGRES_DB:-trackly}"
export POSTGRES_USER="${SPRINT1_DAY2_POSTGRES_USER:-trackly_user}"
export POSTGRES_PASSWORD="${SPRINT1_DAY2_POSTGRES_PASSWORD:-trackly_password}"
export POSTGRES_HOST="${SPRINT1_DAY2_POSTGRES_HOST:-db}"
export POSTGRES_PORT="${SPRINT1_DAY2_POSTGRES_PORT:-5432}"

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trackly_sprint1_day2}"
COMPOSE_OVERRIDE="$(mktemp -t trackly-sprint1-day2-compose.XXXXXX.yml)"
trap 'rm -f "${COMPOSE_OVERRIDE}"' EXIT

cat >"${COMPOSE_OVERRIDE}" <<'YAML'
services:
  web:
    ports: !reset []
  db:
    ports: !reset []
YAML

COMPOSE=(
  docker compose
  -p "${COMPOSE_PROJECT_NAME}"
  -f docker-compose.yml
  -f "${COMPOSE_OVERRIDE}"
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

print_step "Confirm repository root"
pwd

print_step "Confirm required Sprint 1 Day 2 files exist"
test -f requirements.txt
test -f .env.example
test -f docker-compose.yml
test -f config/settings/base.py
test -f config/settings/local.py
test -f config/settings/test.py
test -f README.md
test -f docs/local-setup.md

print_step "Confirm PostgreSQL dependency is present"
run grep -n "psycopg" requirements.txt

print_step "Confirm database environment variables are documented"
run grep -n "POSTGRES_DB" .env.example
run grep -n "POSTGRES_USER" .env.example
run grep -n "POSTGRES_PASSWORD" .env.example
run grep -n "POSTGRES_HOST" .env.example
run grep -n "POSTGRES_PORT" .env.example

print_step "Confirm Docker Compose has PostgreSQL service"
echo
echo "$ ${COMPOSE[*]} config | grep -E \"image: postgres|POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD\""
"${COMPOSE[@]}" config | grep -E "image: postgres|POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD"

print_step "Start database and web services"
run "${COMPOSE[@]}" up -d db web

print_step "Confirm containers are running"
run "${COMPOSE[@]}" ps

print_step "Wait for PostgreSQL to become ready"
for attempt in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    echo "PostgreSQL is ready after ${attempt} attempt(s)."
    break
  fi

  if [ "${attempt}" -eq 30 ]; then
    echo "PostgreSQL did not become ready in time."
    exit 1
  fi

  sleep 1
done

print_step "Confirm PostgreSQL accepts connections"
run "${COMPOSE[@]}" exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

print_step "Confirm Django database engine is PostgreSQL"
run "${COMPOSE[@]}" exec -T web python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
from django.conf import settings

django.setup()

engine = settings.DATABASES["default"]["ENGINE"]
name = settings.DATABASES["default"]["NAME"]
host = settings.DATABASES["default"]["HOST"]
port = settings.DATABASES["default"]["PORT"]

print(f"ENGINE={engine}")
print(f"NAME={name}")
print(f"HOST={host}")
print(f"PORT={port}")

if engine != "django.db.backends.postgresql":
    raise SystemExit("Expected PostgreSQL database engine.")
PY

print_step "Confirm local settings pass Django system check"
run "${COMPOSE[@]}" exec -T web python manage.py check --settings=config.settings.local

print_step "Apply built-in Django migrations"
run "${COMPOSE[@]}" exec -T web python manage.py migrate --settings=config.settings.local

print_step "Confirm database-aware system check passes"
run "${COMPOSE[@]}" exec -T web python manage.py check --database default --settings=config.settings.local

print_step "List applied migration tables"
run "${COMPOSE[@]}" exec -T web python manage.py showmigrations auth contenttypes sessions --settings=config.settings.local

print_step "Confirm PostgreSQL contains Django migration table"
run "${COMPOSE[@]}" exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "\dt django_migrations"

print_step "Confirm local setup documentation mentions PostgreSQL"
run grep -n "PostgreSQL" docs/local-setup.md

print_step "Run final Sprint 1 Day 2 receipt"
run "${COMPOSE[@]}" exec -T web python manage.py check --database default --settings=config.settings.local
echo "Sprint 1 Day 2 PostgreSQL baseline verified"
