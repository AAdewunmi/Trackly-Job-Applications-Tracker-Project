# Trackly: Job Application Tracking and NLP-Based Role Matching Platform

[![CI](https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
[![codecov](https://codecov.io/gh/AAdewunmi/Trackly-Job-Applications-Tracker-Project/branch/main/graph/badge.svg)](https://codecov.io/gh/AAdewunmi/Trackly-Job-Applications-Tracker-Project)
![Code Style](https://img.shields.io/badge/code%20style-black-000000)
![Linting](https://img.shields.io/badge/linting-ruff-purple)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![PostgreSQL](https://img.shields.io/badge/database-postgresql-336791)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A production-minded Django SaaS MVP for tracking job applications and matching
job descriptions against target-role profiles using explainable NLP.

GitHub repository: <https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project>

Trackly helps users register, manage job applications, track application status,
maintain notes, review personal progress, and generate role-fit insights from
job descriptions and stored target-role profiles.

This repository is designed as a realistic SaaS MVP build rather than a toy
CRUD example. It combines Django-rendered templates, Django REST Framework,
PostgreSQL, Docker Compose, GitHub Actions CI, production settings, and
deployment-readiness documentation.

The platform framing is intentional: job application tracking keeps the core SaaS workflow clear, while NLP-based role matching describes the text-processing layer more precisely than a generic AI label. The implemented matching workflow uses NLTK-backed text normalisation, scikit-learn TF-IDF vectorisation, cosine similarity scoring, and explainable overlapping and missing target terms.

Sprint 3 completes the retrieval-style insights workflow on top of the core
job-tracking product: user-owned applications, status validation, notes,
ownership-protected CRUD routes, reusable selectors, service-layer dashboard
metrics, recent activity, secured API endpoints, target role profiles, and
stored explainable job-fit insights. Sprint 1 established the Django,
PostgreSQL, identity, role, authentication, and UI foundation.

## Core MVP Direction

Trackly is designed as a credible early SaaS product, not a toy example. The delivery stance is intentionally simple and production-minded:

- Backend: Django 5
- Frontend: Django-rendered templates, HTMX-ready interactions, and Trackly CSS
- Database: PostgreSQL
- Testing: pytest, pytest-django, factory_boy
- Development workflow: Docker and Docker Compose
- CI: GitHub Actions
- API layer: Django REST Framework under `/api/v1/` with JWT token endpoints
- NLP layer: NLTK preprocessing, TF-IDF cosine comparison, and explainable
  job-fit scoring
- Deployment readiness: production settings, WhiteNoise/Gunicorn dependencies,
  and Render-oriented documentation

## Implemented Through Sprint 3

Trackly currently includes:

- Dockerised Django app and PostgreSQL service
- Environment-driven settings
- Split settings modules for local, test, and production environments
- GitHub Actions CI
- Custom email-first user model
- Role model and role assignment support
- Signup, login, logout, and profile pages
- Authenticated user dashboard
- Protected admin dashboard
- Trackly CSS design system and shared template shell
- User-owned job application create, list, detail, update, and delete flows
- Saved, applied, screening, interviewing, offer, rejected, and withdrawn statuses
- Application notes attached only to user-owned applications
- User-scoped selectors for reusable read queries
- Service-layer dashboard metrics and recent application activity
- Database-backed model, selector, service, view, note, and permission tests
- User-owned target role profiles for retrieval-style matching
- Stored `JobInsight` records linked to job applications and target profiles
- NLTK-backed text preprocessing with deterministic fallback lemmatisation
- scikit-learn TF-IDF cosine similarity scoring
- Explainability fields for extracted terms, overlapping terms, missing target
  terms, and weighted TF-IDF evidence
- Idempotent insight generation for unchanged cleaned inputs and pipeline
  version
- Browser insight workspace for generating and reviewing stored insights
- Secured insights API endpoints for listing and generating/reusing insights
- Custom `403`, `404`, and `500` error templates matching the Trackly design
  system

Hosted Render deployment remains planned work. The repository already includes
the production settings and deployment-readiness documentation needed to support
that work.

## Quick Start

For a repeatable local setup path:

```bash
cp .env.example .env
make build
make up
make migrate
make test
```

The Docker image provisions required NLTK runtime data during build. If a local
container ever reports missing NLTK data, refresh it with:

```bash
make nltk-data
```

Use these docs for the full reviewer path:

- [Local setup](docs/local-setup.md) for environment setup, Docker Compose,
  migrations, and quality checks.
- [Runbook](RUNBOOK.md) for operational commands and troubleshooting.
- [Architecture](docs/architecture.md) for settings modules, app boundaries,
  database choices, and CI expectations.
- [Domain model](docs/domain-model.md) for applications, notes, selectors,
  services, metrics, insights, and ownership rules.
- [Design system](docs/design-system.md) for the Trackly template and CSS
  standard.
- [Sprint runbooks](docs/sprint-runbook/README.md) for historical checkpoint
  scripts and the current Sprint 3 completion check.

## Environment Settings

Trackly keeps environment behaviour isolated through dedicated settings modules:

- Local Docker development uses `config.settings.local`
- Tests and GitHub Actions CI use `config.settings.test`
- ASGI/WSGI deployment uses `config.settings.production`

Shared behaviour lives in `config.settings.base`. Secrets, debug mode, allowed
hosts, CSRF trusted origins, database settings, and production security options
are configured through environment variables. CI also runs migration checks and
Django's production deploy check before tests.

Create a local `.env` from the tracked template before running the app:

```bash
cp .env.example .env
```

The `.env` file is ignored by git and is the place for real local values.
Do not commit generated secret keys, database passwords, service credentials,
or deployment-specific values.

### Required Configuration

| Variable | Local example | Production guidance |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.local` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | Generated local secret | Required unique secret from the deployment secret store |
| `DJANGO_DEBUG` | `True` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | Comma-separated deployed hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | Comma-separated HTTPS origins, including scheme |
| `WEB_PORT` | `8000` | Local Docker Compose host port |
| `POSTGRES_DB` | `trackly` | Production database name |
| `POSTGRES_USER` | `trackly_user` | Production database user |
| `POSTGRES_PASSWORD` | Local-only password | Required database password from the deployment secret store |
| `POSTGRES_HOST` | `db` | Production database host |
| `POSTGRES_PORT` | `5432` | Production database port |

Production settings also read these hardening flags. The defaults are secure
for an HTTPS deployment, but they remain environment-configurable for platform
compatibility:

| Variable | Default |
| --- | --- |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` |
| `DJANGO_SESSION_COOKIE_SECURE` | `True` |
| `DJANGO_CSRF_COOKIE_SECURE` | `True` |
| `DJANGO_SECURE_HSTS_SECONDS` | `31536000` |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` |
| `DJANGO_SECURE_HSTS_PRELOAD` | `True` |
| `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF` | `True` |
| `DJANGO_X_FRAME_OPTIONS` | `DENY` |
| `DJANGO_REFERRER_POLICY` | `same-origin` |

## Repository Structure

```text
.
├── apps/
│   ├── dashboard/          # User/admin dashboard views, metrics services, tests
│   ├── insights/           # Target profiles, job insights, NLP pipeline, UI/API workflow
│   │   ├── api/            # DRF serializers, views, and API routes
│   │   ├── nlp/            # Text preprocessing and TF-IDF similarity helpers
│   │   └── tests/
│   ├── jobs/               # Application tracking domain, browser views, notes
│   │   ├── api/            # DRF serializers, views, and API routes
│   │   └── tests/
│   ├── roles/              # Product roles, permissions, context processors
│   └── users/              # Email-first user model, auth forms, account views
├── config/
│   ├── settings/           # base, local, test, and production settings
│   ├── tests/
│   ├── urls.py
│   ├── views.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/
│   ├── ai-nlp-contract.md
│   ├── api-contract.md
│   ├── architecture.md
│   ├── design-system.md
│   ├── domain-model.md
│   ├── local-setup.md
│   └── sprint-runbook/
├── templates/
│   ├── dashboard/
│   ├── insights/
│   ├── jobs/
│   ├── users/
│   ├── 403.html
│   ├── 404.html
│   ├── 500.html
│   ├── base.html
│   └── home.html
├── static/
│   └── css/
│       └── theme.css
├── .env.example
├── codecov.yml
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── manage.py
├── pyproject.toml
├── pytest.ini
├── RUNBOOK.md
└── requirements.txt
```
