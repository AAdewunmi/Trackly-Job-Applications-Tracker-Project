# Trackly: Job Application Tracking and NLP-Based Role Matching Platform

## Purpose

Trackly is a Django SaaS MVP for tracking job applications and matching job descriptions against target-role profiles using explainable NLP.

The product is structured around authenticated users who own their job application data, manage statuses and notes, review progress in a personal dashboard, and generate deterministic role-fit insights from job descriptions and persisted target-role profiles.

The platform has two core product areas:

- Job application tracking for applications, statuses, notes, and progress.
- NLP-based role matching built around text processing, normalisation, TF-IDF/vector comparison, cosine similarity, and explainable overlapping terms.

The platform framing fits the broader architecture: secured API surfaces, dashboards, stored role profiles, persisted insights, and a workflow that extends beyond a simple tracker.

Sprint 1 establishes the foundation rather than the full feature set. The goal is to create a codebase that can grow safely into the job workflow, API layer, NLP role-matching layer, CI, and deployment work.

## Architectural Style

Trackly uses a modular Django architecture:

- `config/` contains project-level settings, URLs, ASGI, and WSGI entry points.
- `apps/users/` owns identity, custom user behaviour, account forms, and auth views.
- `apps/roles/` owns product roles and permission helpers.
- `apps/dashboard/` owns authenticated dashboard surfaces.
- `templates/` contains server-rendered Django templates.
- `static/` contains lightweight custom assets.
- `docs/` contains architecture, setup, and operational notes.

## Settings Split

The project uses environment-specific settings:

- `config.settings.base` contains shared configuration.
- `config.settings.local` supports local Docker development.
- `config.settings.test` supports pytest and pytest-django.
- `config.settings.production` prepares the app for production hardening.

This split prevents local convenience settings from leaking into deployed environments.

Each environment-specific module imports from `config.settings.base` first, then
overrides only the behaviour that differs for that environment. Secrets, debug
mode, hosts, CSRF trusted origins, database connection values, and production
security options are read from environment variables with explicit defaults for
local or CI usage.

Settings module usage:

- Local Docker: `config.settings.local`
- Tests: `config.settings.test`
- GitHub Actions CI: `config.settings.test`
- ASGI/WSGI deployment entry points: `config.settings.production`
- Production deploy validation: `config.settings.production`

CI enforces the settings split by running:

- Ruff linting
- Black formatting checks
- `makemigrations --check --dry-run` with `config.settings.test`
- `check --deploy` with `config.settings.production`
- pytest with `config.settings.test`

## Database

Trackly uses PostgreSQL from the first sprint. This avoids developing against SQLite assumptions and gives later features realistic persistence behaviour.

Database settings are controlled by environment variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## Identity

Trackly uses a custom user model from Sprint 1. The user signs in with email rather than username. This is intentional because identity decisions become expensive to change after migrations and relations depend on the user model.

The user model also has a many-to-many relationship with `Role`, allowing product-level access control without depending only on Django groups.

## Roles and Access Control

The roles foundation supports:

- `member`
- `admin`

The custom user model has a many-to-many relationship with roles. This creates a
product-specific access-control foundation before protected role-gated workflows
are implemented.

## UI Surface

Sprint 1 uses server-rendered Django templates with HTMX available for
progressive interactions and custom Trackly CSS for styling. The product shell
includes:

- Shared base template
- Navigation
- Flash messages
- Public landing page
- Landing-page product preview, feature, map, pricing, and CTA sections
- Signup page
- Login page
- Profile page
- User dashboard placeholder
- Admin dashboard placeholder

This gives the project a usable product surface before core job application workflow begins.

## Testing Approach

Sprint 1 uses:

- pytest
- pytest-django
- factory_boy
- PostgreSQL-backed database tests

Tests cover:

- User creation
- Email login assumptions
- Role persistence
- Role assignment
- Authentication flows
- Profile access
- Dashboard access
- Landing-page routing and account-aware actions

## Later Sprint Boundaries

Sprint 1 deliberately avoids implementing:

- Job application CRUD
- Application notes
- Dashboard metrics
- API endpoints
- JWT authentication
- NLP-based role matching
- Render deployment
- Role-gated dashboard restrictions

Those features are intentionally staged across later sprints.
