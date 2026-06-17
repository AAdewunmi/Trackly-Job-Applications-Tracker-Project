
---

## `docs/deployment.md`

```markdown
# Trackly Deployment Guide

Trackly is prepared for deployment on Render using Django, Gunicorn, WhiteNoise, and managed PostgreSQL.

## Deployment target

The MVP deployment target is Render because it provides:

- GitHub-backed deploys.
- Managed PostgreSQL.
- Environment variable management.
- Simple web service startup.
- A practical path for portfolio review.

## Production files

Deployment uses:

```text
build.sh
Procfile
config/settings/production.py