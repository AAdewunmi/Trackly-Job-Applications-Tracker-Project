
## `docs/api-contract.md`

```markdown
# Trackly API Contract

## Purpose

Trackly exposes secured API endpoints under `/api/v1/` so the core job application workflow and insight generation workflow can be used by future clients.

The browser UI and API must enforce the same ownership rules.

## Authentication

Trackly uses JWT authentication through SimpleJWT.

Token obtain endpoint:

```text
POST /api/v1/auth/token/