"""Management command for seeding deterministic Trackly demo data."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.insights.services import generate_job_insight
from apps.jobs.models import ApplicationNote, JobApplication
from apps.roles.models import Role


class Command(BaseCommand):
    """Seed deterministic demo users, applications, notes, and insights."""

    help = "Seed repeatable demo data for Trackly."

    DEMO_USERS = [
        {
            "email": "admin.demo@trackly.local",
            "password": "TracklyDemoPass123",
            "first_name": "Admin",
            "last_name": "Demo",
            "role_code": Role.Codes.ADMIN,
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "email": "user.demo@trackly.local",
            "password": "TracklyDemoPass123",
            "first_name": "Maya",
            "last_name": "Demo",
            "role_code": Role.Codes.MEMBER,
            "is_staff": False,
            "is_superuser": False,
        },
        {
            "email": "analyst.demo@trackly.local",
            "password": "TracklyDemoPass123",
            "first_name": "Sam",
            "last_name": "Analyst",
            "role_code": Role.Codes.MEMBER,
            "is_staff": False,
            "is_superuser": False,
        },
        {
            "email": "empty.demo@trackly.local",
            "password": "TracklyDemoPass123",
            "first_name": "Empty",
            "last_name": "State",
            "role_code": Role.Codes.MEMBER,
            "is_staff": False,
            "is_superuser": False,
        },
    ]

    APPLICATIONS = [
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Backend Engineer",
            "title": "Graduate Python Developer",
            "company": "Northstar Software",
            "status": "applied",
            "job_link": "https://example.com/jobs/graduate-python-developer",
            "job_description": (
                "Python Django REST API PostgreSQL Docker testing CI backend "
                "developer role with product delivery focus."
            ),
            "notes": "Application submitted after tailoring CV around Django APIs.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Backend Engineer",
            "title": "Junior Backend Engineer",
            "company": "Harbour Tech",
            "status": "interviewing",
            "job_link": "https://example.com/jobs/junior-backend-engineer",
            "job_description": (
                "Backend engineer role using Python Django PostgreSQL Docker "
                "GitHub Actions and service integration."
            ),
            "notes": "Recruiter screen completed. Technical interview pending.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Backend Engineer",
            "title": "Software Engineer Intern",
            "company": "SignalWorks",
            "status": "saved",
            "job_link": "https://example.com/jobs/software-engineer-intern",
            "job_description": (
                "Software engineering role focused on APIs, clean code, tests, "
                "documentation, and product support."
            ),
            "notes": "Saved for follow-up after reviewing company engineering blog.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Backend Engineer",
            "title": "API Platform Engineer",
            "company": "Cloudlane",
            "status": "screening",
            "job_link": "https://example.com/jobs/api-platform-engineer",
            "job_description": (
                "Platform team building REST APIs, Django services, PostgreSQL "
                "schema design, Docker workflows, and automated regression tests."
            ),
            "notes": "Screening call booked. Prepare API design examples.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Backend Engineer",
            "title": "Backend Product Engineer",
            "company": "BrightPath",
            "status": "offer",
            "job_link": "https://example.com/jobs/backend-product-engineer",
            "job_description": (
                "Python backend product engineering role with Django, API "
                "ownership, PostgreSQL, CI, observability, and feature delivery."
            ),
            "notes": "Offer received. Compare salary, learning scope, and mentorship.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Backend Engineer",
            "title": "Junior Full Stack Developer",
            "company": "MarketGrid",
            "status": "rejected",
            "job_link": "https://example.com/jobs/junior-full-stack-developer",
            "job_description": (
                "Full stack role focused on React, CSS, stakeholder demos, and "
                "lightweight API integration support."
            ),
            "notes": "Rejected after first interview. Save feedback for frontend gaps.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Product Manager",
            "title": "Associate Product Manager",
            "company": "Roadmap Labs",
            "status": "withdrawn",
            "job_link": "https://example.com/jobs/associate-product-manager",
            "job_description": (
                "Product discovery, roadmap planning, user interviews, metrics, "
                "stakeholder communication, and delivery coordination."
            ),
            "notes": "Withdrawn to focus on engineering-track applications.",
        },
        {
            "owner_email": "user.demo@trackly.local",
            "target_profile": "Data Analyst",
            "title": "Data Analyst Graduate Scheme",
            "company": "InsightWorks",
            "status": "saved",
            "job_link": "https://example.com/jobs/data-analyst-graduate",
            "job_description": (
                "SQL dashboards, stakeholder reporting, Python notebooks, data "
                "quality checks, and product analytics."
            ),
            "notes": "Useful comparison role for non-backend target profile.",
        },
        {
            "owner_email": "analyst.demo@trackly.local",
            "target_profile": "Data Analyst",
            "title": "Junior Product Analyst",
            "company": "MetricLoop",
            "status": "applied",
            "job_link": "https://example.com/jobs/junior-product-analyst",
            "job_description": (
                "Product analytics role using SQL, Python, dashboards, experiment "
                "analysis, and stakeholder reporting."
            ),
            "notes": "Applied with portfolio dashboard link included.",
        },
        {
            "owner_email": "analyst.demo@trackly.local",
            "target_profile": "Data Analyst",
            "title": "Operations Data Assistant",
            "company": "Northbank Health",
            "status": "interviewing",
            "job_link": "https://example.com/jobs/operations-data-assistant",
            "job_description": (
                "Operational reporting, Excel, SQL data checks, process metrics, "
                "and weekly dashboard maintenance."
            ),
            "notes": (
                "Interview panel confirmed. Prepare SQL joins and dashboard examples."
            ),
        },
    ]

    TARGET_PROFILES = [
        {
            "owner_email": "user.demo@trackly.local",
            "title": "Backend Engineer",
            "description": (
                "Python, Django, APIs, PostgreSQL, Docker, CI, testing, and "
                "backend product delivery."
            ),
            "keywords": [
                "python",
                "django",
                "postgresql",
                "docker",
                "api",
                "testing",
                "ci",
                "backend",
            ],
        },
        {
            "owner_email": "user.demo@trackly.local",
            "title": "Data Analyst",
            "description": (
                "SQL, Python, dashboards, analytics, reporting, stakeholder "
                "communication, and data quality."
            ),
            "keywords": [
                "sql",
                "python",
                "dashboard",
                "analytics",
                "reporting",
                "stakeholder",
                "data",
            ],
        },
        {
            "owner_email": "user.demo@trackly.local",
            "title": "Product Manager",
            "description": (
                "Product discovery, roadmap planning, user research, metrics, "
                "prioritisation, and delivery coordination."
            ),
            "keywords": [
                "product",
                "roadmap",
                "discovery",
                "metrics",
                "stakeholder",
                "delivery",
            ],
        },
        {
            "owner_email": "analyst.demo@trackly.local",
            "title": "Data Analyst",
            "description": (
                "SQL, Python, dashboards, product analytics, data quality, and "
                "clear stakeholder reporting."
            ),
            "keywords": [
                "sql",
                "python",
                "dashboard",
                "analytics",
                "reporting",
                "data",
            ],
        },
    ]

    def handle(self, *args, **options):
        """Create deterministic demo records and keep repeated runs idempotent."""
        call_command("seed_roles")

        users_by_email = {}
        for user_data in self.DEMO_USERS:
            user = self._upsert_user(user_data)
            self._assign_role(user, user_data["role_code"])
            users_by_email[user.email] = user

        profiles_by_owner_and_title = {}
        for profile_data in self.TARGET_PROFILES:
            profile = self._upsert_target_profile(
                owner=users_by_email[profile_data["owner_email"]],
                profile_data=profile_data,
            )
            profiles_by_owner_and_title[(profile.owner.email, profile.title)] = profile

        created_applications = []
        for offset, application_data in enumerate(self.APPLICATIONS):
            owner = users_by_email[application_data["owner_email"]]
            target_profile = profiles_by_owner_and_title[
                (owner.email, application_data["target_profile"])
            ]
            application = self._upsert_application(
                owner=owner,
                application_data=application_data,
                days_ago=offset,
            )
            self._upsert_note(application, application_data["notes"])
            self._upsert_insight(application, target_profile)
            created_applications.append(application)

        self.stdout.write(self.style.SUCCESS("Trackly demo data seeded successfully."))
        self.stdout.write("Demo accounts:")
        for user_data in self.DEMO_USERS:
            self.stdout.write(f"  {user_data['email']} / {user_data['password']}")
        self.stdout.write(f"Demo applications available: {len(created_applications)}")

    def _upsert_user(self, user_data):
        """Create or update a demo user and set a deterministic password."""
        User = get_user_model()
        user, _created = User.objects.update_or_create(
            email=user_data["email"],
            defaults={
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "is_staff": user_data["is_staff"],
                "is_superuser": user_data["is_superuser"],
                "is_active": True,
            },
        )
        user.set_password(user_data["password"])
        user.save(update_fields=["password", "is_staff", "is_superuser", "is_active"])
        return user

    def _assign_role(self, user, role_code):
        """Assign an active product role to a demo user."""
        role = Role.objects.get(code=role_code, is_active=True)
        user.roles.add(role)

    def _upsert_target_profile(self, owner, profile_data):
        """Create or update the demo target role profile."""
        profile, _created = TargetRoleProfile.objects.update_or_create(
            owner=owner,
            title=profile_data["title"],
            defaults={
                "description": profile_data["description"],
                "keywords": profile_data["keywords"],
                "is_active": True,
            },
        )
        return profile

    def _upsert_application(self, owner, application_data, days_ago):
        """Create or update a deterministic demo job application."""
        applied_date = timezone.localdate() - timedelta(days=days_ago)

        application, _created = JobApplication.objects.update_or_create(
            owner=owner,
            company=application_data["company"],
            title=application_data["title"],
            defaults={
                "status": application_data["status"],
                "job_link": application_data["job_link"],
                "job_description": application_data["job_description"],
                "notes": application_data["notes"],
                "applied_date": applied_date,
            },
        )
        return application

    def _upsert_note(self, application, note_body):
        """Create a deterministic note for a demo application."""
        ApplicationNote.objects.update_or_create(
            application=application,
            body=note_body,
            defaults={"body": note_body},
        )

    def _upsert_insight(self, application, target_profile):
        """Generate or reuse a retrieval-style sample insight."""
        JobInsight.objects.filter(
            job_application=application,
            target_profile=target_profile,
        ).delete()
        generate_job_insight(application, target_profile)
