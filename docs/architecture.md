# Trackly: Job Application Tracking and NLP-Based Role Matching Platform

## Purpose

Trackly is a Django SaaS MVP for tracking job applications and matching job
descriptions against target-role profiles using explainable NLP.

Sprint 3 extends the completed core job-tracking workflow with a
retrieval-style insights app. Authenticated users can own applications, manage
statuses and notes, review recent activity, see user-scoped dashboard metrics,
store target-role profiles, and generate explainable job-fit insights using
NLTK preprocessing, scikit-learn TF-IDF vectorisation, cosine similarity, and
weighted overlapping or missing target terms.

## Architectural Style

Trackly uses a modular Django architecture:

- `config/` contains project-level settings, URLs, ASGI, and WSGI entry points.
- `apps/users/` owns identity, account forms, and authentication views.
- `apps/roles/` owns product roles and permission helpers.
- `apps/jobs/` owns job applications, notes, forms, selectors, services, and
  workflow views.
- `apps/dashboard/` owns the user dashboard service context and dashboard
  surfaces.
- `apps/insights/` owns target role profiles, persisted job insights, NLP
  preprocessing, TF-IDF similarity scoring, and insight generation services.
- `templates/` contains server-rendered Django templates.
- `static/` contains Trackly CSS and other lightweight assets.
- `docs/` contains architecture, setup, domain, design, and operational notes.

## Settings Split

The project uses environment-specific settings:

- `config.settings.base` contains shared configuration.
- `config.settings.local` supports local Docker development.
- `config.settings.test` supports pytest and pytest-django.
- `config.settings.production` prepares the app for production hardening.

Each environment-specific module imports from `config.settings.base`, then
overrides only the behaviour that differs for that environment. Secrets, debug
mode, hosts, CSRF trusted origins, database connection values, and production
security options are read from environment variables with explicit defaults
for local or CI usage.

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
- pytest with branch coverage for `apps`
- Codecov upload from `coverage.xml`

## Database

Trackly uses PostgreSQL from the first sprint. Local Docker Compose and CI use
`postgres:16-alpine`.

Database settings are controlled by environment variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## Identity

Trackly uses a custom user model introduced in Sprint 1. Users sign in with
email rather than username. The user model has a many-to-many relationship with
`Role`, allowing product-level access control without depending only on Django
groups.

## Roles and Access Control

The roles foundation supports:

- `member`
- `admin`

The user dashboard at `/dashboard/` requires authentication. The admin dashboard
at `/dashboard/admin/` requires authentication and passes users through the
Trackly admin permission helper.

Job application list, detail, update, delete, and note creation flows require
authentication. Detail-level operations fetch applications through an
owner-scoped selector, so a user attempting to access another user's record
receives a 404 response.

## Job Tracking Domain

Trackly implements:

- User-owned `JobApplication` records
- Explicit saved, applied, screening, interviewing, offer, rejected, and
  withdrawn statuses
- Validation for required title and company fields, valid statuses, valid
  optional URLs, and non-future applied dates
- Inline internal notes on each application
- Timeline-style `ApplicationNote` records owned through their parent
  application
- Reusable selectors for user-scoped application and note reads
- Service-layer dashboard metric aggregation

See `docs/domain-model.md` for the complete contract.

## Insights Domain

Sprint 3 implements:

- User-owned `TargetRoleProfile` records with normalised keyword lists.
- Persisted `JobInsight` records linked to a job application and target role
  profile.
- A single supported pipeline version: `nltk-tfidf-cosine-v1`.
- NLTK-backed preprocessing with deterministic fallback lemmatisation.
- scikit-learn TF-IDF vectorisation and cosine similarity scoring.
- Score labels derived from rounded cosine similarity values.
- Explainability fields for extracted terms, overlapping terms, missing target
  terms, and weighted TF-IDF evidence.
- Idempotent insight generation using a source hash derived from cleaned job
  text, cleaned target text, and pipeline version.

The insight service requires an active target role profile and enforces that
the selected job application and target profile share the same owner.

See `docs/ai-nlp-contract.md` for the complete NLP contract.

## UI Surface

Trackly uses server-rendered Django templates with HTMX available for
progressive interactions and custom Trackly CSS for styling. The implemented
surface includes:

- Shared base template, navigation, footer, and flash messages
- Public landing page
- Signup, login, logout, and profile flows
- Application list, create, detail, update, delete, and note creation flows
- User dashboard with dynamic pipeline, progress metrics, and recent
  applications
- Protected admin dashboard shell

The dashboard includes an AI/NLP Insights panel as a product surface. The
backend insight persistence and generation services are implemented in
`apps.insights`; full browser workflows for managing target profiles and
displaying generated insight history remain a later UI integration boundary.

## Testing Approach

Trackly uses pytest, pytest-django, factory_boy, and PostgreSQL-backed database
tests.

Current coverage includes:

- Custom users, roles, authentication flows, profile access, and landing routes
- Job application model validation and admin registration
- User-scoped selectors and metric services
- Application list, create, detail, update, delete, and note workflows
- Cross-user permission enforcement
- Dashboard metric context, recent applications, protected access, admin
  permissions, and authentication behaviour
- Job application API endpoints, nested note API endpoints, JWT authentication,
  and API ownership boundaries
- Target role profiles, persisted job insights, NLTK preprocessing, TF-IDF
  cosine scoring, weighted explainability evidence, source-hash idempotency,
  and NLTK runtime-data failure handling

## Later Sprint Boundaries

The following remain planned:

- Insights API endpoints and browser workflows for target profile management
  and generated insight history
- Production deployment to Render
