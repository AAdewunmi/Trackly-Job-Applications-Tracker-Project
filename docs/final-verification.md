# Trackly Final Verification Checklist

This checklist marks the release-readiness checkpoint for the Trackly SaaS MVP.
Use it after local development work and before treating a branch, PR, or Render
deployment as reviewed.

## Local Verification

Start from a clean local environment:

```bash
cp .env.example .env
make build
make up
make migrate
make seed
```

Then run the full local quality gate:

```bash
make check
```

`make check` currently runs:

- Ruff linting.
- Black formatting check.
- Migration drift check with `config.settings.test`.
- Django production deployment check with `config.settings.production`.
- Pytest inside the Docker web container.

Expected outcome:

- Docker image builds successfully.
- Web and PostgreSQL containers start successfully.
- Migrations apply successfully.
- Deterministic showcase data seeds without duplicating records.
- Ruff passes.
- Black formatting check passes.
- Migration check reports no missing migrations.
- Production deploy check has no critical blockers.
- Full test suite passes.

## Focused Verification Commands

Use these commands when checking one part of the release:

```bash
make test
make lint
make format-check
make migrations-check
make deploy-check
```

For a focused insights regression check:

```bash
docker compose exec -T web pytest apps/insights
```

Do not record a fixed expected test count in this document. The passing count
will change as the test suite grows.

## Health Endpoint Verification

Local:

```text
GET http://localhost:8000/health/
```

Live:

```text
GET https://<your-render-service>.onrender.com/health/
```

Expected response:

```json
{
  "status": "ok",
  "service": "trackly",
  "release": "...",
  "timestamp": "..."
}
```

Expected outcome:

- HTTP `200`.
- `status` is `ok`.
- `service` is `trackly`.
- `release` matches the local or deployed environment.
- `timestamp` is present.

## Product Verification

Confirm the browser workflow:

- Public home page loads at `/`.
- User can register.
- User can log in.
- User can log out.
- User can view profile.
- Member user can open `/dashboard/`.
- Admin user can open `/dashboard/admin/`.
- Member user can create a job application.
- Member user can list only their own applications.
- Member user can view their own application detail page.
- Member user can update their own application.
- Member user can delete their own application.
- Member user can add and edit notes on their own applications.
- Dashboard metrics reflect stored user-scoped data.
- User can create or use a target role profile.
- User can generate a job insight.
- User can view stored insights.
- Another user's product data is not accessible.
- Custom `403`, `404`, and `500` templates render through the Trackly shell.

## API Verification

Confirm the current secured API surface:

```text
POST /api/v1/auth/token/
POST /api/v1/auth/token/refresh/
GET  /api/v1/jobs/applications/
POST /api/v1/jobs/applications/
GET  /api/v1/jobs/applications/<id>/
PUT  /api/v1/jobs/applications/<id>/
PATCH /api/v1/jobs/applications/<id>/
DELETE /api/v1/jobs/applications/<id>/
GET  /api/v1/jobs/applications/<id>/notes/
POST /api/v1/jobs/applications/<id>/notes/
GET  /api/v1/jobs/applications/<id>/notes/<note_id>/
PUT  /api/v1/jobs/applications/<id>/notes/<note_id>/
PATCH /api/v1/jobs/applications/<id>/notes/<note_id>/
DELETE /api/v1/jobs/applications/<id>/notes/<note_id>/
GET  /api/v1/insights/
POST /api/v1/insights/generate/
```

Expected outcome:

- JWT token endpoint returns access and refresh tokens for valid credentials.
- Secured API endpoints reject unauthenticated requests.
- Authenticated job API requests are scoped to the current user.
- Authenticated note API requests are scoped through the parent application.
- Authenticated insight API requests are scoped to the current user.
- Insight generation requires a user-owned job application and active
  user-owned target role profile.

## AI/NLP Verification

Confirm the deterministic insight workflow:

- Target role profiles are user-owned.
- `JobInsight` records are linked to a job application and target role profile.
- Pipeline version is `nltk-tfidf-cosine-v1`.
- NLTK preprocessing produces cleaned job and target text.
- TF-IDF cosine scoring produces a rounded similarity score.
- Score labels follow the documented thresholds.
- Output includes extracted terms, overlapping terms, missing target terms,
  weighted TF-IDF evidence, source hash, and explanation.
- Re-running generation for unchanged cleaned input reuses the stored insight.
- Missing NLTK runtime data produces an actionable developer error.

## CI Verification

Confirm the GitHub Actions workflow passes on the reviewed branch.

The current workflow runs:

- Dependency installation on Python 3.12.
- PostgreSQL 16 service startup.
- Django startup settings and database connectivity check.
- Ruff.
- Black `--check`.
- Django system check with `config.settings.test`.
- `makemigrations --check --dry-run`.
- Migrations.
- Prepared schema verification.
- Production settings check with `check --deploy`.
- Production static-file collection with `collectstatic --noinput`.
- Pytest with branch coverage for `apps`.
- Codecov upload from `coverage.xml`.

Expected outcome:

- Required check `CI Pipeline / Lint, format, and test` passes.
- No migration drift is reported.
- Production settings load with deploy-check environment values.
- Static files collect under production settings.
- Coverage XML is generated and uploaded.

## Deployment Verification

Confirm deployment configuration exists and matches the current Render target:

- `render.yaml` defines `trackly-web`.
- `render.yaml` defines managed PostgreSQL database `trackly-db`.
- `DATABASE_URL` is wired from `trackly-db`.
- `DJANGO_SETTINGS_MODULE` is `config.settings.production`.
- Render runs migrations, collects static files, and starts Gunicorn.
- `healthCheckPath` is `/health/`.
- Production hardening flags are environment-driven.

After deploying, run the smoke checks in `docs/deployment.md`.

## Documentation Verification

Confirm reviewer-facing docs are present and current:

- `README.md`
- `docs/local-setup.md`
- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/ai-nlp-contract.md`
- `docs/deployment.md`
- `docs/ci.md`
- `docs/domain-model.md`
- `docs/design-system.md`
- `docs/demo-script.md`
- `docs/final-verification.md`

Expected outcome:

- Setup, testing, deployment, architecture, API, AI/NLP behaviour, limitations,
  and demo flow are documented.
- Demo script uses current routes, commands, seeded accounts, and review flow.
- Final verification checklist uses current Makefile and CI commands.

## Release Tag

Create and push a release tag only after local verification, CI verification,
documentation review, and deployment smoke checks are complete.

```bash
git tag v0.1.0-mvp
git push origin v0.1.0-mvp
```

## Completion Statement

Trackly is release-ready when the app is reproducible locally, verified by CI,
deployable on Render, documented for reviewers, smoke-tested through the
browser and API surfaces, and tagged as the first MVP release.
