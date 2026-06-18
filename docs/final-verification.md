Verification

Run insight tests with:

docker compose exec web pytest apps/insights -q

---

## `docs/final-verification.md`

```markdown
# Trackly Final Verification Checklist

This checklist marks the Sprint 4 release-readiness checkpoint for the Trackly SaaS MVP.

## Local verification

Run:

```bash
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_roles
docker compose exec web python manage.py seed_demo_data
docker compose exec web python manage.py check
docker compose exec web ruff check .
docker compose exec web black --check .
docker compose exec web pytest -q

Expected receipts:

System check identified no issues (0 silenced).
All checks passed!
48 passed
Production-style verification

Run:

docker compose exec web python manage.py check --deploy --settings=config.settings.production
docker compose exec web python manage.py collectstatic --noinput --settings=config.settings.production

Expected outcome:

Production settings load.
Static files collect.
No critical deployment blockers remain.
Health endpoint verification

Local:

GET http://localhost:8000/health/

Live:

GET https://your-render-url.onrender.com/health/

Expected:

HTTP 200

Expected response includes:

status=ok
service=trackly
release
timestamp
Product verification

Confirm:

User can register.
User can log in.
User can log out.
User can view profile.
User can open personal dashboard.
Admin can open admin dashboard.
User can create a job application.
User can list own applications.
User can view own application detail.
User can update own application.
User can delete own application.
User can add a note to own application.
Dashboard metrics reflect stored data.
User can create or use a target role profile.
User can generate a job insight.
User can view stored insights.
Another user's data is not accessible.
API verification

Confirm:

/api/v1/auth/token/ returns JWT tokens for valid credentials.
Secured API endpoints reject unauthenticated requests.
Authenticated job API requests are user-scoped.
Authenticated insight API requests are user-scoped.
CI verification

Confirm the GitHub Actions workflow passes on the latest main branch.

The CI pipeline must run:

ruff
black check
Django check
migrations
pytest
Release tag

Create the MVP release tag:

git tag v0.1.0-mvp

Push the release tag:

git push origin v0.1.0-mvp
Completion statement

Trackly Sprint 4 is complete when the app is reproducible locally, verified by CI, deployable on Render, documented for reviewers, and tagged as the first MVP release.


---

# Final Sprint Verification Checklist

Sprint 4 is complete when all of the following are true:

- Docker Compose builds successfully.
- Web and PostgreSQL containers start successfully.
- Migrations run inside the container.
- `seed_roles` runs without duplicating records.
- `seed_demo_data` runs without duplicating demo data.
- Full test suite passes.
- Ruff passes.
- Black formatting check passes.
- Django system check passes.
- Production deployment check has no critical blockers.
- Static files collect under production settings.
- `/health/` returns HTTP 200.
- GitHub Actions CI completes successfully.
- Render deployment is configured.
- Live product flow is verified.
- README explains setup, testing, API, AI/NLP behaviour, deployment, and limitations.
- Demo script is ready.
- Final verification document is complete.
- Release tag `v0.1.0-mvp` is created and pushed.