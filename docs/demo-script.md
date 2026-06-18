# Trackly Demo Script

This demo script presents Trackly as a production-minded Django SaaS MVP for
job application tracking and deterministic AI/NLP job-fit insights.

## Demo Goal

Show that Trackly is more than a CRUD app. It supports identity, protected
user workflows, user-scoped dashboard metrics, secured API access,
deterministic AI/NLP insights, Docker-based setup, CI, and Render deployment
readiness.

A strong walkthrough should take 6 to 8 minutes. Start with the product flow,
then use the engineering evidence to explain why the build is credible.

## Before The Demo

For a local walkthrough, prepare the app with the deterministic showcase data:

```bash
cp .env.example .env
make build
make up
make migrate
make seed
```

The seed command is idempotent. It creates baseline roles, demo users,
applications across every workflow status, notes, target role profiles, and
persisted job insights generated through the current insight service.

Demo accounts use the password `TracklyDemoPass123`:

| Account | Purpose |
| --- | --- |
| `admin.demo@trackly.local` | Admin dashboard and platform metrics |
| `user.demo@trackly.local` | Populated job-search workspace |
| `analyst.demo@trackly.local` | Second member account for ownership isolation |
| `empty.demo@trackly.local` | Empty-state account |

For a deployed walkthrough, use the Render service URL and start with the
health check:

```text
GET /health/
```

The response should include `status`, `service`, `release`, and `timestamp`.

## Opening Narrative

Trackly helps users register, manage job applications, track application
status, maintain notes, review personal progress, and compare job descriptions
against stored target-role profiles.

The build focuses on practical software delivery: tested domain behaviour,
ownership rules, API access, explainable AI output, reproducible local setup,
CI, and deployment readiness.

## Demo Path

### 1. Product Surface

Open the app home page:

```text
/
```

Explain that the public page leads into a server-rendered Django product
surface backed by PostgreSQL, not static mock screens.

### 2. Authentication

Register a new user or log in with:

```text
user.demo@trackly.local / TracklyDemoPass123
```

Show that authenticated users have their own workspace. Mention that admin
users are routed to the protected admin dashboard while member users remain in
the end-user workflow.

### 3. User Dashboard

Open:

```text
/dashboard/
```

Highlight:

- Total applications.
- Active applications.
- Interviews.
- Offers.
- Rejections.
- Recent applications and activity.
- AI/NLP Insights panel.

Explain that dashboard metrics are built through service-layer queries scoped
to the authenticated user.

### 4. Job Applications

Open:

```text
/applications/
```

Show:

- User-owned application list.
- Empty-state behaviour with `empty.demo@trackly.local`, if useful.
- Create application flow at `/applications/new/`.
- Detail page.
- Update flow.
- Delete confirmation.

Explain that detail-level operations use owner-scoped selectors, so another
user's application is not exposed.

### 5. Notes

Open an application detail page and add or edit a note.

Explain that notes capture workflow context that a status field alone cannot
hold. Notes are owned through their parent application and follow the same
user-ownership boundary.

### 6. AI/NLP Insights

Open:

```text
/insights/
```

Generate or review a stored job insight.

Highlight:

- Target role profile.
- Extracted terms.
- Overlapping terms.
- Missing target terms.
- Weighted TF-IDF evidence.
- Similarity score and score label.
- Plain-English explanation.
- Source hash and pipeline version.

Explain that the insight engine is deterministic and explainable by design. It
uses NLTK preprocessing, scikit-learn TF-IDF vectorisation, cosine similarity,
stored source hashes, and idempotent reuse when cleaned source text is
unchanged.

### 7. API Surface

Explain the secured API surface:

```text
POST /api/v1/auth/token/
POST /api/v1/auth/token/refresh/
GET  /api/v1/jobs/applications/
POST /api/v1/jobs/applications/
GET  /api/v1/jobs/applications/<id>/
GET  /api/v1/jobs/applications/<id>/notes/
GET  /api/v1/insights/
POST /api/v1/insights/generate/
```

Mention that unauthenticated requests are rejected and authenticated requests
are scoped to the current user. Insight generation requires a user-owned job
application and an active user-owned target role profile.

### 8. Admin Dashboard

If showing the admin path, log in with:

```text
admin.demo@trackly.local / TracklyDemoPass123
```

Open:

```text
/dashboard/admin/
```

Highlight platform metrics, recent activity, status visualisation, and the
searchable/filterable application management table. Explain that this route
uses Trackly's admin permission helper and is separate from the member
workspace.

### 9. Engineering Evidence

Show the repeatable local quality gate:

```bash
make check
```

For focused checks, mention:

```bash
make test
make lint
make format-check
make migrations-check
make deploy-check
```

Explain that GitHub Actions runs equivalent checks with PostgreSQL 16, Ruff,
Black, Django startup and migration checks, production deploy checks, pytest,
coverage output, and Codecov upload.

### 10. Deployment Evidence

Point to:

- `render.yaml`
- `config.settings.production`
- `docs/deployment.md`

Explain that Render uses the blueprint to create the Docker web service,
managed PostgreSQL database, production environment variables, Gunicorn startup
command, static collection, migrations, and `/health/` operational check.

## Closing Narrative

Trackly is intentionally scoped as a first SaaS MVP. The value is not that it
solves every job-search workflow. The value is that the core product behaviour
is built with real engineering boundaries: authentication, ownership,
persistence, tests, API contracts, explainable AI output, Docker workflow, CI,
and deployment readiness.

## Demo Risks To Avoid

- Do not spend too long on implementation details before showing the product
  flow.
- Do not describe the AI/NLP feature as predictive hiring intelligence. It is a
  deterministic retrieval-style matching workflow.
- Do not run showcase seed data against production data.
- Do not imply cross-user data is shareable; current product records are scoped
  to their owner.
