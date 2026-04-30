#!/usr/bin/env bash
#
# Sprint 1 Day 1 foundation verification for Trackly.
#
# Run from the repository root:
#
#   ./docs/sprint-runbook/sprint-1/sprint-1-day-1.sh
#
# The script fails fast when a required file, service, setting, or version check
# does not match the expected Sprint 1 Day 1 foundation.

set -euo pipefail

EXPECTED_DJANGO_VERSION="5.1.15"
EXPECTED_COMPOSE_PROJECT="trackly-job-applications-tracker-project"

# Print a readable section header before each verification block.
step() {
  printf "\n==> %s\n" "$1"
}

# Fail if a required project file is missing.
require_file() {
  local path="$1"

  if [[ ! -f "$path" ]]; then
    printf "Missing required file: %s\n" "$path" >&2
    exit 1
  fi
}

# Run a command and fail if its output does not exactly match the expected text.
require_output() {
  local expected="$1"
  shift

  local actual
  actual="$("$@")"

  if [[ "$actual" != "$expected" ]]; then
    printf "Unexpected output for command: %s\n" "$*" >&2
    printf "Expected: %s\n" "$expected" >&2
    printf "Actual: %s\n" "$actual" >&2
    exit 1
  fi

  printf "%s\n" "$actual"
}

step "Confirm repository root"
pwd

# Core project files required before Sprint 1 feature work continues.
step "Confirm required Sprint 1 Day 1 files exist"
required_root_files=(
  "README.md"
  "manage.py"
  "requirements.txt"
  "pyproject.toml"
  ".env.example"
  "Dockerfile"
  "docker-compose.yml"
)

for file in "${required_root_files[@]}"; do
  require_file "$file"
done

# Django entry points and environment-specific settings modules.
step "Confirm Django config files exist"
required_config_files=(
  "config/urls.py"
  "config/wsgi.py"
  "config/asgi.py"
  "config/settings/base.py"
  "config/settings/local.py"
  "config/settings/test.py"
  "config/settings/production.py"
)

for file in "${required_config_files[@]}"; do
  require_file "$file"
done

# Architecture docs should exist before implementation expands.
step "Confirm documentation files exist"
require_file "docs/architecture.md"

# Compose should resolve to the expected project name and web/db services.
step "Validate Docker Compose configuration"
docker compose config | grep -E "^(name:|services:|  db:|  web:|    image: postgres:16-alpine|    build:)"
require_output "name: ${EXPECTED_COMPOSE_PROJECT}" sh -c "docker compose config | sed -n '1p'"

# Build and start the local Docker services used for verification.
step "Build the containers"
docker compose build

step "Start the services"
docker compose up -d

# Both services must be running before Django checks can be trusted.
step "Confirm containers are running"
docker compose ps
docker compose ps --services --filter status=running | grep -Fx "db"
docker compose ps --services --filter status=running | grep -Fx "web"

# Local settings are used by Docker Compose and local development.
step "Confirm local settings load"
docker compose exec -T web python manage.py check --settings=config.settings.local

# Force the settings module assignment so the Compose default does not leak in.
step "Confirm production settings import without starting the server"
docker compose exec -T web python -c "import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'; import django; django.setup(); print('production settings import ok')"

# Test settings should import independently of local settings.
step "Confirm test settings import without starting the server"
docker compose exec -T web python -c "import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'; import django; django.setup(); print('test settings import ok')"

# Keep this pinned to requirements.txt so dependency drift is visible.
step "Confirm Django version inside container"
require_output "$EXPECTED_DJANGO_VERSION" docker compose exec -T web python -m django --version

# Architecture documentation should clearly describe Trackly.
step "Confirm architecture documentation has Trackly scope"
grep -n "Trackly" docs/architecture.md

# Final receipt for console logs and PR notes.
step "Run final Sprint 1 Day 1 receipt"
docker compose exec -T web python manage.py check --settings=config.settings.local
printf "Sprint 1 Day 1 foundation verified\n"
