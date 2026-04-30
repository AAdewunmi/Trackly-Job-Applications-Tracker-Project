# Trackly Architecture

## Purpose

Trackly is a Django SaaS MVP for job application tracking. The product is structured around authenticated users who own their job application data, review progress in a personal dashboard, and later generate deterministic AI/NLP job-fit insights.

Sprint 1 establishes the foundation rather than the full feature set. The goal is to create a codebase that can grow safely into the job workflow, API layer, AI/NLP layer, CI, and deployment work.

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

The admin dashboard accepts either:

- Django staff users
- Users with the active Trackly admin role

This keeps the MVP practical while still creating a product-specific access-control path.

## UI Surface

Sprint 1 uses server-rendered Django templates with Bootstrap. The product shell includes:

- Shared base template
- Navigation
- Flash messages
- Signup page
- Login page
- Profile page
- User dashboard
- Admin dashboard

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
- Admin dashboard restrictions

## Later Sprint Boundaries

Sprint 1 deliberately avoids implementing:

- Job application CRUD
- Application notes
- Dashboard metrics
- API endpoints
- JWT authentication
- AI/NLP insights
- CI
- Render deployment

Those features are intentionally staged across later sprints.