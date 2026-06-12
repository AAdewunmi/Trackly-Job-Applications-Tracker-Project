# Trackly API Contract

## Purpose

Trackly exposes authenticated API endpoints under `/api/v1/` as the API layer is
introduced alongside the existing server-rendered product routes.

The browser UI and API must enforce the same ownership rules: users may only
read or mutate records they own, and admin-only surfaces must continue to use
Trackly's role and staff permission checks.

## Current API Surface

The configured API surface currently includes JWT authentication endpoints,
user-owned job application endpoints, application note endpoints, and
retrieval-style insight endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/token/` | Obtain access and refresh tokens. |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh an access token. |
| `GET` | `/api/v1/jobs/applications/` | List the authenticated user's job applications. |
| `POST` | `/api/v1/jobs/applications/` | Create a job application owned by the authenticated user. |
| `GET` | `/api/v1/jobs/applications/<id>/` | Retrieve one user-owned job application. |
| `PUT` | `/api/v1/jobs/applications/<id>/` | Replace one user-owned job application. |
| `PATCH` | `/api/v1/jobs/applications/<id>/` | Partially update one user-owned job application. |
| `DELETE` | `/api/v1/jobs/applications/<id>/` | Delete one user-owned job application. |
| `GET` | `/api/v1/jobs/applications/<id>/notes/` | List notes for one user-owned job application. |
| `POST` | `/api/v1/jobs/applications/<id>/notes/` | Add a note to one user-owned job application. |
| `GET` | `/api/v1/jobs/applications/<id>/notes/<note_id>/` | Retrieve one note on a user-owned job application. |
| `PUT` | `/api/v1/jobs/applications/<id>/notes/<note_id>/` | Replace one note on a user-owned job application. |
| `PATCH` | `/api/v1/jobs/applications/<id>/notes/<note_id>/` | Partially update one note on a user-owned job application. |
| `DELETE` | `/api/v1/jobs/applications/<id>/notes/<note_id>/` | Delete one note on a user-owned job application. |
| `GET` | `/api/v1/insights/` | List stored job insights for the authenticated user. |
| `POST` | `/api/v1/insights/generate/` | Generate or reuse a job insight for one user-owned application and active target profile. |

## Authentication

Trackly uses Django REST Framework with SimpleJWT.

API requests authenticate with a bearer token:

```text
Authorization: Bearer <access-token>
```

The default API permission is authenticated access. Session authentication is
also enabled so API views can support the existing Django-authenticated browser
context where appropriate.

## Existing Browser Routes

The current browser application routes remain:

| Path | Purpose |
| --- | --- |
| `/` | Home page. |
| `/accounts/` | User authentication and account routes. |
| `/applications/` | Job application workflow. |
| `/applications/notes/<id>/edit/` | Job application note update workflow. |
| `/applications/notes/<id>/delete/` | Job application note delete workflow. |
| `/dashboard/` | Authenticated user dashboard. |
| `/insights/` | Browser insights dashboard and generation workflow. |
| `/admin/` | Django admin. |

## API Resource Notes

Job application API endpoints are registered under `/api/v1/jobs/applications/`.
Application note API endpoints are nested under their parent application. Both
resource groups use the same user ownership boundary as the browser job
application workflow.

Insight API endpoints are registered under `/api/v1/insights/`. The list
endpoint returns only stored insights connected to applications owned by the
authenticated user.

The generation endpoint accepts this JSON payload:

```json
{
  "job_application_id": 1,
  "target_profile_id": 2
}
```

Both IDs must reference records owned by the authenticated user, and the target
profile must be active. Foreign applications or target profiles return `404` so
ownership boundaries are not exposed.

The generation response returns `201 Created` when a new `JobInsight` record is
created and `200 OK` when unchanged source content reuses an existing insight.
The response body includes:

- `created`: whether this request created a new stored insight.
- `insight`: the stored retrieval-style insight output.

Insight output includes the related application and target profile IDs/titles,
pipeline version, source hash, filtered user-facing extracted terms,
overlapping terms, missing target terms, weighted TF-IDF evidence, similarity
score, score label, plain-English explanation, and creation timestamp.

The simple term lists follow the same presentation policy as the browser UI:
readable single terms and approved useful phrases are shown, while mechanical
TF-IDF bigrams are suppressed. Complete weighted evidence remains available in
`top_overlapping_weighted_terms` and `missing_weighted_target_terms` for API
consumers that need audit/detail data.
