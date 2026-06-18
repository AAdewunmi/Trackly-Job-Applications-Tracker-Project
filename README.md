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
- Deterministic showcase seed data for local review, screenshots, and manual
  QA

Hosted Render deployment is described by the root `render.yaml` blueprint. It
provisions the Docker web service, managed PostgreSQL database, production
environment variables, and `/health/` operational check used by Render and
post-release smoke tests. See [Deployment](docs/deployment.md) for the
GitHub-to-Render Blueprint workflow and post-deploy product smoke checklist.

## Quick Start

For a repeatable local setup path:

```bash
cp .env.example .env
make build
make up
make migrate
make seed
make test
```

The Docker image provisions required NLTK runtime data during build. If a local
container ever reports missing NLTK data, refresh it with:

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
   tests, coverage, and production deploy checks.
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
7. Review extracted terms, overlapping terms, missing target terms, similarity
   score, score label, weighted evidence, and explanation.
8. Use `/api/v1/` endpoints for authenticated programmatic access where useful.

The seeded `user.demo@trackly.local` account gives reviewers a populated
workspace. The seeded `empty.demo@trackly.local` account shows the empty-state
experience.

## Documentation Coverage

These docs are part of the reviewer-facing documentation set:

- [Local setup](docs/local-setup.md) for environment setup, Docker Compose,
  migrations, seeded data, and local reproducibility.
- [Runbook](RUNBOOK.md) for operational commands and troubleshooting.
- [Architecture](docs/architecture.md) for settings modules, app boundaries,
  request surfaces, ownership model, database choices, and CI expectations.
- [API contract](docs/api-contract.md) for authenticated API routes, JWT
  access, payloads, response semantics, and ownership rules.
- [AI/NLP contract](docs/ai-nlp-contract.md) for feature inputs, non-goals,
  deterministic pipeline behaviour, score labels, explanation output, and
  known AI/NLP boundaries.
- [Deployment](docs/deployment.md) for Render Blueprint configuration,
  production settings, static-file collection, health checks, smoke checks,
  logging, troubleshooting, and deployment growth limits.
- [CI pipeline](docs/ci.md) for GitHub Actions triggers, PostgreSQL setup,
  Django startup checks, migrations, linting, formatting, tests, and coverage.
- [Domain model](docs/domain-model.md) for applications, notes, selectors,
  services, metrics, insights, and ownership rules.
- [Design system](docs/design-system.md) for the Trackly template and CSS
  standard.
- [Demo script](docs/demo-script.md) for a concise product walkthrough that
  connects the browser flow, API, AI/NLP feature, CI, and deployment story.
- [Final verification](docs/final-verification.md) for release-readiness checks
  across local setup, product behaviour, API, AI/NLP, CI, deployment, and docs.
- [Sprint runbooks](docs/sprint-runbook/README.md) for historical checkpoint
  scripts and the current Sprint 3 completion check.

Coverage map:

| Area | Documentation |
| --- | --- |
| Setup | `README.md`, `docs/local-setup.md`, `RUNBOOK.md` |
| Testing | `README.md`, `docs/ci.md`, `docs/final-verification.md` |
| Deployment | `docs/deployment.md`, `docs/final-verification.md`, `render.yaml` |
| Architecture | `docs/architecture.md`, `docs/domain-model.md` |
| API | `docs/api-contract.md`, `docs/domain-model.md` |
| AI/NLP | `docs/ai-nlp-contract.md`, `docs/demo-script.md` |
| Limitations and non-goals | `docs/ai-nlp-contract.md`, `docs/deployment.md`, README Future Extensions |

## Demo Data

Trackly includes deterministic showcase seed data for local review:

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

## CI Pipeline

Trackly uses GitHub Actions as the repository quality gate. The required check
is `CI Pipeline / Lint, format, and test`.

The pipeline installs dependencies, provisions PostgreSQL 16, verifies Django
startup settings and database connectivity, runs Ruff and Black checks, validates
and applies migrations, verifies the prepared schema, runs production deploy
checks, executes pytest against `config.settings.test`, and uploads coverage to
Codecov.

Reviewers should expect a passing pipeline to prove that the project can install
from a clean checkout, boot Django with test settings, prepare the PostgreSQL
schema, satisfy lint and format rules, pass regression tests, and meet the
configured coverage gate.

See [CI pipeline](docs/ci.md) for the full reviewer and contributor reference.

## Future Extensions

After the MVP is complete, Trackly could be extended with:

- LLM-assisted CV and cover letter tailoring based on a selected job
  application, target profile, and stored job-fit insight.
- LLM-generated interview preparation packs with likely questions, company
  research prompts, STAR story suggestions, and follow-up email drafts.
- Semantic search using embeddings so users can search across job descriptions,
  notes, target profiles, and generated insights by meaning rather than keyword
  matching alone.
- Hybrid matching that combines the current deterministic TF-IDF evidence with
  optional embedding similarity or LLM reasoning while preserving explainable
  source terms.
- Contact and recruiter tracking with relationship history, follow-up reminders,
  and communication notes.
- Calendar and email integrations for interview scheduling, deadline reminders,
  and automatic follow-up tasks.
- Analytics for job-search conversion rates, time in each pipeline stage,
  company response patterns, and target-role fit over time.
- Team or mentor review workflows where a user can share selected applications
  and insights for feedback without exposing the whole account.
- Browser extension or job-board import flow to save roles directly into
  Trackly from external job listings.
- Subscription, billing, and account-plan features if Trackly evolves from MVP
  into a multi-tenant SaaS product.
- Deployment-hardening tasks such as CI Docker image builds and lightweight
  browser smoke/E2E checks for signup, login, dashboard, applications, and
  insights before an active production launch.

## Environment Settings

Trackly keeps environment behaviour isolated through dedicated settings modules:

- Local Docker development uses `config.settings.local`
- Tests and GitHub Actions CI use `config.settings.test`
- ASGI/WSGI deployment uses `config.settings.production`

Shared behaviour lives in `config.settings.base`. Secrets, debug mode, allowed
hosts, CSRF trusted origins, database settings, and production security options
are configured through environment variables. CI also runs migration checks and
Django's production deploy check before tests.

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
`release=<RELEASE_VERSION>` so Render logs can be filtered during operational
review. Use `LOG_LEVEL` and `DJANGO_LOG_LEVEL` to temporarily increase
verbosity while debugging a release.

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
├── render.yaml
├── Makefile
├── manage.py
├── pyproject.toml
├── pytest.ini
├── RUNBOOK.md
└── requirements.txt
```
