# Trackly: Job Application Tracking and NLP-Based Role Matching Platform

[![Build](https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![Code Style](https://img.shields.io/badge/code%20style-black-000000)
![Licence](https://img.shields.io/badge/licence-MIT-lightgrey)
[![codecov](https://codecov.io/gh/AAdewunmi/Trackly-Job-Applications-Tracker-Project/branch/main/graph/badge.svg)](https://codecov.io/gh/AAdewunmi/Trackly-Job-Applications-Tracker-Project)
![Linting](https://img.shields.io/badge/linting-ruff-purple)
![PostgreSQL](https://img.shields.io/badge/database-postgresql-336791)

Trackly is a production-minded Django SaaS MVP for tracking job applications
and generating deterministic, explainable NLP job-fit insights against stored
target-role profiles.

GitHub repository: <https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project>

The product helps users manage a job-search pipeline, maintain notes, review
dashboard metrics, compare job descriptions with target role profiles, and
understand why a role appears to be a stronger or weaker fit. The implementation
uses server-rendered Django views for the core workflow, Django REST Framework
for secured API access, PostgreSQL for persistence, Docker Compose for local
runtime, GitHub Actions for CI, and a Render blueprint for deployment readiness.

## MVP Scope

Trackly currently includes:

- Email-first custom user model.
- Role-aware member and admin access control.
- Signup, login, logout, and profile pages.
- Authenticated user dashboard with user-scoped metrics and recent activity.
- Protected admin dashboard with platform metrics and application management.
- User-owned job application create, list, detail, update, and delete flows.
- Saved, applied, screening, interviewing, offer, rejected, and withdrawn
  workflow statuses.
- Application notes attached to user-owned applications.
- User-scoped selectors and service-layer business logic.
- Target role profiles for retrieval-style job matching.
- Stored `JobInsight` records linked to applications and target profiles.
- NLTK preprocessing with deterministic fallback lemmatisation.
- scikit-learn TF-IDF vectorisation and cosine similarity scoring.
- Explainability fields for extracted terms, overlapping terms, missing target
  terms, weighted TF-IDF evidence, score labels, and explanations.
- Idempotent insight generation for unchanged cleaned inputs and pipeline
  version.
- Browser insight workspace and application-detail insight generation.
- Secured API endpoints under `/api/v1/` with JWT token support.
- Custom `403`, `404`, and `500` templates that reuse the Trackly shell.
- Deterministic showcase seed data for local review and demos.
- PostgreSQL-backed tests, CI quality gates, production settings checks,
  production static-file collection checks, and Render deployment config.

## Stack

- Backend: Django 5
- API: Django REST Framework and SimpleJWT
- Frontend: Django templates, HTMX-ready server-rendered flows, Trackly CSS
- Database: PostgreSQL
- NLP: NLTK, scikit-learn TF-IDF, cosine similarity
- Tests: pytest, pytest-django, factory_boy, pytest-cov
- Quality: Ruff, Black, coverage gate, GitHub Actions
- Runtime: Docker, Docker Compose, Gunicorn, WhiteNoise
- Deployment target: Render Blueprint with managed PostgreSQL

## Quick Start

For the repeatable local Docker path:

```bash
cp .env.example .env
make build
make up
make migrate
make seed
make test
```

The app runs at:

```text
http://localhost:8000
```

The Docker image provisions the required NLTK runtime data during build. If a
local container reports missing NLTK data, refresh it with:

```bash
make nltk-data
```

## How To Use The Repo

Use this repository as a reproducible Django SaaS MVP build:

1. Start with [Local setup](docs/local-setup.md) to configure `.env`, build the
   Docker services, run migrations, seed deterministic demo data, and execute
   local checks.
2. Use the Makefile for normal development commands: `make build`, `make up`,
   `make migrate`, `make seed`, `make test`, `make lint`, `make format-check`,
   `make migrations-check`, `make deploy-check`, and `make check`.
3. Use [CI pipeline](docs/ci.md) to understand the GitHub Actions quality gate,
   PostgreSQL setup, startup checks, migration checks, formatting, linting,
   tests, coverage, production deploy checks, and production static collection.
4. Use [Final verification](docs/final-verification.md) before treating a
   branch, PR, or deployment as reviewed.
5. Use [Demo script](docs/demo-script.md) when presenting the MVP to a
   technical reviewer.

## How To Use Trackly

Use Trackly as a job-search workspace:

1. Sign up or log in.
2. Review the user dashboard at `/dashboard/`.
3. Create and manage job applications at `/applications/`.
4. Add notes to application detail pages to preserve workflow context.
5. Create or use a target role profile from the insights workspace.
6. Generate deterministic job-fit insights at `/insights/` or from an
   application detail page.
7. Review extracted terms, overlapping terms, missing target terms, weighted
   evidence, similarity score, score label, and explanation.
8. Use `/api/v1/` endpoints for authenticated programmatic access where useful.

The seeded `user.demo@trackly.local` account gives reviewers a populated
workspace. The seeded `empty.demo@trackly.local` account shows the empty-state
experience.

## Demo Data

Trackly includes deterministic showcase seed data:

```bash
make seed
```

The seed command creates repeatable demo accounts, baseline roles, job
applications across every workflow status, application notes, target role
profiles, and persisted retrieval-style insights generated through the current
NLP service. It is idempotent, so repeated runs update the same deterministic
records instead of duplicating them.

If you need to load a Django fixture instead of the deterministic showcase
dataset, use the Makefile wrapper around Django's `loaddata` command:

```bash
make loaddata FIXTURE=path/to/fixture.json
```

Demo accounts use the password `TracklyDemoPass123`:

| Account | Purpose |
| --- | --- |
| `admin.demo@trackly.local` | Admin dashboard and platform metrics |
| `user.demo@trackly.local` | Populated job-search workspace with applications, notes, target profiles, and insights |
| `analyst.demo@trackly.local` | Second member account for cross-user isolation and alternate profile data |
| `empty.demo@trackly.local` | Empty-state account for setup and onboarding screens |

The showcase dataset is intended for local development, screenshots, manual QA,
and reviewer walkthroughs. Do not run it against production data.

## CI And Verification

Trackly uses GitHub Actions as the repository quality gate. The required check
is:

```text
CI Pipeline / Lint, format, and test
```

The pipeline installs dependencies, provisions PostgreSQL 16, verifies Django
startup settings and database connectivity, runs Ruff and Black checks, validates
and applies migrations, verifies the prepared schema, runs production deploy
checks, verifies production static-file collection, executes pytest against
`config.settings.test`, writes coverage output, and uploads coverage to Codecov.

Use the local quality gate before opening or reviewing a PR:

```bash
make check
```

For a CI-style test run inside Docker:

```bash
docker compose exec web python -m pytest --ds=config.settings.test --cov=apps --cov-report=xml
```

## Documentation Coverage

The documentation set is intended to make the build understandable,
reproducible, reviewable, and easy to discuss with technical reviewers.

| Area | Documentation |
| --- | --- |
| Setup | [Local setup](docs/local-setup.md), [Runbook](RUNBOOK.md), this README |
| Testing and CI | [CI pipeline](docs/ci.md), [Final verification](docs/final-verification.md), this README |
| Deployment | [Deployment](docs/deployment.md), [Final verification](docs/final-verification.md), `render.yaml` |
| Architecture | [Architecture](docs/architecture.md), [Domain model](docs/domain-model.md) |
| API | [API contract](docs/api-contract.md), [Domain model](docs/domain-model.md) |
| AI/NLP | [AI/NLP contract](docs/ai-nlp-contract.md), [Demo script](docs/demo-script.md) |
| Product demo | [Demo script](docs/demo-script.md), [Final verification](docs/final-verification.md) |
| Limitations and non-goals | [AI/NLP contract](docs/ai-nlp-contract.md), [Deployment](docs/deployment.md), Potential Extensions below |

Key docs:

- [Architecture](docs/architecture.md) defines settings modules, app
  boundaries, request surfaces, ownership model, database choices, and CI
  expectations.
- [API contract](docs/api-contract.md) defines authenticated API routes, JWT
  access, payloads, response semantics, and ownership rules.
- [AI/NLP contract](docs/ai-nlp-contract.md) defines feature inputs, non-goals,
  deterministic pipeline behaviour, score labels, explanation output, and
  AI/NLP boundaries.
- [Deployment](docs/deployment.md) defines Render Blueprint configuration,
  production settings, static-file collection, health checks, smoke checks,
  logging, troubleshooting, and deployment growth limits.
- [Demo script](docs/demo-script.md) provides a concise walkthrough connecting
  the browser flow, API, AI/NLP feature, CI, and deployment story.
- [Final verification](docs/final-verification.md) gives a release-readiness
  checklist across local setup, product behaviour, API, AI/NLP, CI, deployment,
  and docs.

## Environment Settings

Trackly keeps environment behaviour isolated through dedicated settings modules:

- Local Docker development uses `config.settings.local`
- Tests and GitHub Actions CI use `config.settings.test`
- ASGI/WSGI deployment uses `config.settings.production`

Shared behaviour lives in `config.settings.base`. Secrets, debug mode, allowed
hosts, CSRF trusted origins, database settings, and production security options
are configured through environment variables. CI also runs migration checks,
Django's production deploy check, and production static-file collection before
tests.

Render deployment configuration lives in `render.yaml`. The blueprint runs the
Docker image with Gunicorn, applies migrations, collects static files, wires
`DATABASE_URL` from the managed `trackly-db` PostgreSQL service, and exposes
`/health/` as the service health check path. The deployment guide documents the
GitHub-backed Render Blueprint workflow and live MVP route checks to run after
deployment.

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
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | Required comma-separated deployed hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | Comma-separated HTTPS origins, including scheme |
| `WEB_PORT` | `8000` | Local Docker Compose host port |
| `DATABASE_URL` | `postgres://trackly_user:...@db:5432/trackly` | Required production database URL from the deployment platform |
| `POSTGRES_DB` | `trackly` | Local Docker Compose database name |
| `POSTGRES_USER` | `trackly_user` | Local Docker Compose database user |
| `POSTGRES_PASSWORD` | Local-only password | Local Docker Compose database password |
| `POSTGRES_HOST` | `db` | Local Docker Compose database host |
| `POSTGRES_PORT` | `5432` | Local Docker Compose host port |

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
| `LOG_LEVEL` | `INFO` |
| `DJANGO_LOG_LEVEL` | `INFO` |

For the default Render blueprint, `DJANGO_ALLOWED_HOSTS` is `.onrender.com` and
`DJANGO_CSRF_TRUSTED_ORIGINS` is `https://*.onrender.com`. Update both values
in `render.yaml` when attaching a custom production domain.

Production logs are written to stdout/stderr for platform log capture. Each log
line includes timestamp, logger, module, process/thread IDs, message, and
`release=<RELEASE_VERSION>` so deployment logs can be filtered during
operational review.

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── apps/
│   ├── dashboard/          # User/admin dashboards, services, URLs, tests
│   ├── insights/           # Target profiles, job insights, NLP, UI/API, tests
│   │   ├── api/
│   │   ├── migrations/
│   │   ├── nlp/
│   │   └── tests/
│   ├── jobs/               # Applications, notes, selectors, services, UI/API, tests
│   │   ├── api/
│   │   ├── management/
│   │   ├── migrations/
│   │   └── tests/
│   ├── roles/              # Product roles, permissions, seed command, tests
│   │   ├── management/
│   │   ├── migrations/
│   │   └── tests/
│   └── users/              # Email-first user model, auth forms, account views, tests
│       ├── migrations/
│       └── tests/
├── config/
│   ├── settings/           # base, local, test, and production settings
│   ├── tests/              # health, production settings, render blueprint tests
│   ├── urls.py
│   ├── views.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/
│   ├── ai-nlp-contract.md
│   ├── api-contract.md
│   ├── architecture.md
│   ├── ci.md
│   ├── demo-script.md
│   ├── deployment.md
│   ├── design-system.md
│   ├── domain-model.md
│   ├── final-verification.md
│   ├── local-setup.md
│   └── sprint-runbook/
├── static/
│   ├── css/
│   └── img/
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
├── .env.example
├── codecov.yml
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── Makefile
├── manage.py
├── pyproject.toml
├── pytest.ini
├── README.md
├── render.yaml
├── requirements.txt
└── RUNBOOK.md
```

## Potential Extensions

The MVP intentionally keeps the product focused. Natural next steps include:

- LLM-assisted CV and cover letter tailoring based on a selected job
  application, target profile, and stored job-fit insight.
- LLM-generated interview preparation packs.
- Semantic search across job descriptions, notes, target profiles, and
  generated insights.
- Hybrid matching that combines deterministic TF-IDF evidence with optional
  embedding similarity or LLM reasoning.
- Contact and recruiter tracking.
- Calendar and email integrations for interview scheduling and reminders.
- Analytics for conversion rates, time in pipeline stages, company response
  patterns, and target-role fit over time.
- Team or mentor review workflows for selected applications and insights.
- Browser extension or job-board import flow.
- Subscription, billing, and account-plan features for a multi-tenant SaaS
  product.
- Deployment-hardening tasks such as CI Docker image builds and lightweight
  browser smoke/E2E checks before an active production launch.
