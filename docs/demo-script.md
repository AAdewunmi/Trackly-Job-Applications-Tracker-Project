
---

## `docs/demo-script.md`

```markdown
# Trackly Demo Script

This demo script presents Trackly as a production-minded SaaS MVP for job application tracking.

## Demo goal

Show that Trackly is more than a CRUD app. It supports identity, protected user workflows, dashboard metrics, secured API access, deterministic AI/NLP insights, Docker-based setup, CI, and deployment readiness.

## Opening narrative

Trackly is a Django SaaS MVP for managing job applications and generating lightweight job-fit insights. The product helps users track their application pipeline, keep notes, review progress, and compare job descriptions against a target role profile.

The build focuses on practical software delivery: tested domain behaviour, ownership rules, API access, explainable AI outputs, reproducible local setup, CI, and deployment readiness.

## Demo path

### 1. Start with the product surface

Open the deployed app.

Show:

```text
/health/

2. Register or log in

Use the demo account:

user.demo@trackly.local / TracklyDemoPass123

Explain that users have their own dashboard and protected workflows.

3. Show the dashboard

Open the user dashboard and highlight:

Total applications.
Active applications.
Interviews.
Offers.
Rejections.
Recent activity.

Explain that the dashboard is backed by persisted user data, not static cards.

4. Show job applications

Open the applications list.

Show:

User-owned applications.
Empty state behaviour if using a fresh account.
Create application flow.
Detail page.
Update flow.
Delete protection through ownership tests.
5. Show notes

Open an application detail page and add a note.

Explain that notes capture workflow context that a status field alone cannot hold.

6. Show AI/NLP insight generation

Generate or review a job insight.

Highlight:

Extracted keywords.
Matched keywords.
Missing keywords.
Similarity score.
Explanation.
Source text hash.

Explain that the insight engine is deterministic and explainable by design.

7. Show API access

Explain the secured API surface:

POST /api/v1/auth/token/
/api/v1/jobs/
/api/v1/insights/

Mention that unauthenticated requests are rejected and authenticated requests are scoped to the current user.

8. Show engineering evidence

Mention:

docker compose exec web pytest -q
docker compose exec web ruff check .
docker compose exec web black --check .
docker compose exec web python manage.py check --deploy --settings=config.settings.production

Explain that CI runs equivalent checks on GitHub Actions.

Closing narrative

Trackly is intentionally scoped as a first SaaS MVP. The value is not that it solves every job-search workflow. The value is that the core product behaviour is built with real engineering boundaries: authentication, ownership, persistence, tests, API contracts, explainable AI output, Docker workflow, CI, and deployment readiness.

Suggested demo duration

A strong walkthrough should take 6 to 8 minutes.

Demo risks to avoid

Do not spend too long on implementation details before showing the product flow. Start with the user journey, then use the engineering evidence to explain why the build is credible.