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

A Django SaaS MVP for tracking job applications and matching job descriptions against target-role profiles using explainable NLP.

GitHub repository: <https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project>

Trackly helps users register, manage job applications, track application status,
maintain notes, and review personal progress. The planned NLP layer will generate
role-fit insights from job descriptions and stored target-role profiles.

The platform framing is intentional: job application tracking keeps the core SaaS workflow clear, while NLP-based role matching describes the text-processing layer more precisely than a generic AI label. The matching workflow is designed around text normalisation, TF-IDF/vector comparison, cosine similarity, and explainable overlapping terms.

Sprint 2 completes the core job-tracking workflow: user-owned applications,
status validation, notes, ownership-protected CRUD routes, reusable selectors,
service-layer dashboard metrics, and recent application activity. Sprint 1
established the Django, PostgreSQL, identity, role, authentication, and UI
foundation.

## Core MVP Direction

Trackly is designed as a credible early SaaS product, not a toy example. The delivery stance is intentionally simple and production-minded:

- Backend: Django 5
- Frontend: Django-rendered templates, HTMX-ready interactions, and Trackly CSS
- Database: PostgreSQL
- Testing: pytest, pytest-django, factory_boy
- Development workflow: Docker and Docker Compose
- Future API layer: Django REST Framework under `/api/v1/`
- NLP layer: deterministic keyword extraction, target-role profile comparison, and explainable job-fit scoring
- Deployment target: Render

## Implemented Through Sprint 2

Trackly currently includes:

- Dockerised Django app and PostgreSQL service
- Environment-driven settings
- Split settings modules for local, test, and production environments
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
- Temporary unauthenticated dashboard preview at `/dashboard/preview/`
- Database-backed model, selector, service, view, note, and permission tests

The explainable NLP matching workflow, API layer, JWT authentication, and Render
deployment remain planned work.

## Quick Start

For a repeatable local setup path:

```bash
cp .env.example .env
make build
make up
make migrate
make test
```

Use these docs for the full reviewer path:

- [Local setup](docs/local-setup.md) for environment setup, Docker Compose,
  migrations, and quality checks.
- [Runbook](RUNBOOK.md) for operational commands and troubleshooting.
- [Architecture](docs/architecture.md) for settings modules, app boundaries,
  database choices, and CI expectations.
- [Domain model](docs/domain-model.md) for Sprint 2 applications, notes,
  selectors, services, metrics, and ownership rules.
- [Design system](docs/design-system.md) for the Trackly template and CSS
  standard.
- [Sprint runbooks](docs/sprint-runbook/README.md) for historical checkpoint
  scripts and the current Sprint 2 completion check.

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
│   ├── dashboard/
│   ├── jobs/
│   ├── roles/
│   └── users/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/
│   ├── architecture.md
│   ├── design-system.md
│   ├── domain-model.md
│   ├── local-setup.md
│   └── sprint-runbook/
├── .env.example
├── static/
├── templates/
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── manage.py
├── pyproject.toml
├── RUNBOOK.md
└── requirements.txt
```
