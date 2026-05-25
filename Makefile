SHELL := /bin/sh

COMPOSE := docker compose
WEB := $(COMPOSE) exec web
WEB_T := $(COMPOSE) exec -T web
MANAGE := $(WEB) python manage.py
MANAGE_T := $(WEB_T) python manage.py

.DEFAULT_GOAL := help

.PHONY: help build up down restart logs shell dbshell migrate migrations superuser test lint format format-check check deploy-check clean

help:
	@echo "Trackly development commands"
	@echo ""
	@echo "  make build         Build Docker images"
	@echo "  make up            Start services"
	@echo "  make down          Stop services"
	@echo "  make restart       Restart services"
	@echo "  make logs          Follow web logs"
	@echo "  make shell         Open Django shell"
	@echo "  make dbshell       Open Django database shell"
	@echo "  make migrate       Apply database migrations"
	@echo "  make migrations    Create Django migrations"
	@echo "  make superuser     Create a Django superuser"
	@echo "  make test          Run pytest"
	@echo "  make lint          Run Ruff"
	@echo "  make format        Format with Black and Ruff"
	@echo "  make format-check  Check formatting"
	@echo "  make check         Run lint, format-check, migrations check, deploy check, and tests"
	@echo "  make clean         Remove Python and test cache files"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f web

shell:
	$(MANAGE) shell

dbshell:
	$(MANAGE) dbshell

migrate:
	$(MANAGE) migrate

migrations:
	$(MANAGE) makemigrations

superuser:
	$(MANAGE) createsuperuser

test:
	$(WEB_T) pytest

lint:
	$(WEB_T) python -m ruff check .

format:
	$(WEB_T) python -m ruff check . --fix
	$(WEB_T) python -m black .

format-check:
	$(WEB_T) python -m black . --check

migrations-check:
	$(MANAGE_T) makemigrations --check --dry-run --settings=config.settings.test

deploy-check:
	$(MANAGE_T) check --deploy --settings=config.settings.production

check: lint format-check migrations-check deploy-check test

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
