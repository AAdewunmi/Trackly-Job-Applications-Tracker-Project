# Trackly: Job Application Tracking and NLP-Based Role Matching Platform

[![CI](https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
[![codecov](https://codecov.io/gh/AAdewunmi/Trackly-Job-Applications-Tracker-Project/branch/main/graph/badge.svg)](https://codecov.io/gh/AAdewunmi/Trackly-Job-Applications-Tracker-Project)
![Code Style](https://img.shields.io/badge/code%20style-black-000000)
![Linting](https://img.shields.io/badge/linting-ruff-purple)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![PostgreSQL](https://img.shields.io/badge/database-postgresql-336791)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A Django SaaS MVP for tracking job applications and matching job descriptions against target-role profiles using explainable NLP.

GitHub repository: <https://github.com/AAdewunmi/Trackly-Job-Applications-Tracker-Project>

Trackly helps users register, manage job applications, track application status, maintain notes, review personal progress, and generate role-fit insights from job descriptions and stored target-role profiles.

The platform framing is intentional: job application tracking keeps the core SaaS workflow clear, while NLP-based role matching describes the text-processing layer more precisely than a generic AI label. The matching workflow is designed around text normalisation, TF-IDF/vector comparison, cosine similarity, and explainable overlapping terms.

Sprint 1 establishes the product foundation: Django project structure, PostgreSQL-backed local development, custom email-first users, role support, authentication flows, protected dashboards, Bootstrap templates, and database-backed tests.

## Core MVP Direction

Trackly is designed as a credible early SaaS product, not a toy example. The delivery stance is intentionally simple and production-minded:

- Backend: Django 5
- Frontend: Django templates, Bootstrap 5, lightweight custom CSS
- Database: PostgreSQL
- Testing: pytest, pytest-django, factory_boy
- Development workflow: Docker and Docker Compose
- Future API layer: Django REST Framework under `/api/v1/`
- NLP layer: deterministic keyword extraction, target-role profile comparison, and explainable job-fit scoring
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

## Environment Settings

Trackly keeps environment behavior isolated through dedicated settings modules:

- Local Docker development uses `config.settings.local`
- Tests and GitHub Actions CI use `config.settings.test`
- ASGI/WSGI deployment uses `config.settings.production`

Shared behavior lives in `config.settings.base`. Secrets, debug mode, allowed
hosts, CSRF trusted origins, database settings, and production security options
are configured through environment variables. CI also runs migration checks and
Django's production deploy check before tests.

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
