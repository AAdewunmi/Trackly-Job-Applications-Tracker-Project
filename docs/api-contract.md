# Trackly API Contract

## Purpose

Trackly exposes authenticated API endpoints under `/api/v1/` as the API layer is
introduced alongside the existing server-rendered product routes.

The browser UI and API must enforce the same ownership rules: users may only
read or mutate records they own, and admin-only surfaces must continue to use
Trackly's role and staff permission checks.

## Current API Surface

The configured API surface currently includes JWT authentication endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/token/` | Obtain access and refresh tokens. |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh an access token. |

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
| `/dashboard/` | Authenticated user dashboard. |
| `/admin/` | Django admin. |

## Planned API Resources

Job application API endpoints are planned under `/api/v1/` once serializers,
viewsets, API URL modules, and tests are added. No jobs API route is currently
registered in `config.urls`.

Insights API endpoints are also planned work. The project does not currently
include an `apps.insights` Django app, so no insights routes are registered.
