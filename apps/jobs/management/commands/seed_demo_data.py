"""Management command for seeding deterministic Trackly demo data."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.insights.models import TargetRoleProfile
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
            "first_name": "User",
            "last_name": "Demo",
            "role_code": Role.Codes.MEMBER,
            "is_staff": False,
            "is_superuser": False,
        },
    ]

    APPLICATIONS = [
        {
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
    ]

    TARGET_PROFILE = {
        "title": "Graduate Software Engineer",
        "description": (
            "Demo target profile for Python, Django, APIs, PostgreSQL, Docker, "
            "CI, testing, and backend delivery."
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
    }

    def handle(self, *args, **options):
        """Create deterministic demo records and keep repeated runs idempotent."""
        call_command("seed_roles")

        admin_user = self._upsert_user(self.DEMO_USERS[0])
        demo_user = self._upsert_user(self.DEMO_USERS[1])

        self._assign_role(admin_user, Role.Codes.ADMIN)
        self._assign_role(demo_user, Role.Codes.MEMBER)

        target_profile = self._upsert_target_profile(demo_user)

        created_applications = []
        for offset, application_data in enumerate(self.APPLICATIONS):
            application = self._upsert_application(
                owner=demo_user,
                application_data=application_data,
                days_ago=offset,
            )
            self._upsert_note(application, application_data["notes"])
            self._upsert_insight(application, target_profile)
            created_applications.append(application)

        self.stdout.write(self.style.SUCCESS("Trackly demo data seeded successfully."))
        self.stdout.write("Demo accounts:")
        self.stdout.write("  admin.demo@trackly.local / TracklyDemoPass123")
        self.stdout.write("  user.demo@trackly.local / TracklyDemoPass123")
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

    def _upsert_target_profile(self, owner):
        """Create or update the demo target role profile."""
        profile, _created = TargetRoleProfile.objects.update_or_create(
            owner=owner,
            title=self.TARGET_PROFILE["title"],
            defaults={
                "description": self.TARGET_PROFILE["description"],
                "keywords": self.TARGET_PROFILE["keywords"],
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
        generate_job_insight(application, target_profile)
