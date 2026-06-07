# Trackly API Contract

## Purpose

Trackly exposes authenticated API endpoints under `/api/v1/` as the API layer is
introduced alongside the existing server-rendered product routes.

The browser UI and API must enforce the same ownership rules: users may only
read or mutate records they own, and admin-only surfaces must continue to use
Trackly's role and staff permission checks.

## Current API Surface

The configured API surface currently includes JWT authentication endpoints and
user-owned job application endpoints:

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
| `/admin/` | Django admin. |

## API Resource Notes

Job application API endpoints are registered under `/api/v1/jobs/applications/`.
Application note API endpoints are nested under their parent application. Both
resource groups use the same user ownership boundary as the browser job
application workflow.

Insights API endpoints are also planned work. The project does not currently
include an `apps.insights` Django app, so no insights routes are registered.
