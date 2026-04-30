# Trackly-Django-App

![CI Pipeline](https://img.shields.io/badge/CI-pending-lightgrey)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey)
![Code Style](https://img.shields.io/badge/code%20style-black-000000)
![Linting](https://img.shields.io/badge/linting-ruff-purple)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![PostgreSQL](https://img.shields.io/badge/database-postgresql-336791)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Trackly-Django-App is a production-minded SaaS MVP for job application tracking.

The product helps users register, manage job applications, track application status, review personal progress, and later generate lightweight AI/NLP insights from job descriptions and target-role profiles.

Sprint 1 establishes the product foundation: Django project structure, PostgreSQL-backed local development, custom email-first users, role support, authentication flows, protected dashboards, Bootstrap templates, and database-backed tests.

## Core MVP Direction

Trackly is designed as a credible early SaaS product, not a toy example. The delivery stance is intentionally simple and production-minded:

- Backend: Django 5
- Frontend: Django templates, Bootstrap 5, lightweight custom CSS
- Database: PostgreSQL
- Testing: pytest, pytest-django, factory_boy
- Development workflow: Docker and Docker Compose
- Future API layer: Django REST Framework under `/api/v1/`
- Future AI/NLP layer: deterministic keyword extraction and explainable job-fit scoring
- Deployment target: Render

## Sprint 1 Capabilities

Sprint 1 delivers:

- Dockerised Django app and PostgreSQL service
- Environment-driven settings
- Split settings modules for local, test, and production environments
- Custom email-first user model
- Role model and role assignment support
- Signup, login, logout, and profile pages
- Authenticated user dashboard
- Protected admin dashboard
- Bootstrap base template and navigation
- Initial documentation
- Model and integration tests

## Repository Structure

```text
.
├── apps/
│   ├── dashboard/
│   ├── roles/
│   └── users/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/
├── static/
├── templates/
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pyproject.toml
└── requirements.txt
