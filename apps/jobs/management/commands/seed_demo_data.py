"""Management command for seeding deterministic Trackly demo data."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.insights.models import JobInsight
from apps.insights.models import TargetRoleProfile
from apps.jobs.models import ApplicationNote
from apps.jobs.models import JobApplication
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
            "role_slug": "admin",
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "email": "user.demo@trackly.local",
            "password": "TracklyDemoPass123",
            "first_name": "User",
            "last_name": "Demo",
            "role_slug": "user",
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
        "role_title": "Graduate Software Engineer",
        "target_keywords": [
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

        self._assign_role(admin_user, "admin")
        self._assign_role(demo_user, "user")

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

    def _assign_role(self, user, role_slug):
        """Assign a role to a demo user when the user model exposes a role field."""
        role = Role.objects.get(slug=role_slug)

        # The earlier sprint role model is intentionally simple. This branch keeps
        # the seed command compatible with either a direct FK or M2M role design.
        if hasattr(user, "role"):
            user.role = role
            user.save(update_fields=["role"])
        elif hasattr(user, "roles"):
            user.roles.add(role)

    def _upsert_target_profile(self, owner):
        """Create or update the demo target role profile."""
        defaults = self._model_defaults(
            TargetRoleProfile,
            {
                "role_title": self.TARGET_PROFILE["role_title"],
                "title": self.TARGET_PROFILE["role_title"],
                "target_keywords": self.TARGET_PROFILE["target_keywords"],
                "keywords": self.TARGET_PROFILE["target_keywords"],
                "description": (
                    "Demo target profile for Python, Django, APIs, PostgreSQL, "
                    "Docker, CI, and backend delivery."
                ),
            },
        )

        lookup = self._owner_lookup(TargetRoleProfile, owner)
        title_field = self._first_existing_field(
            TargetRoleProfile,
            ["role_title", "title", "name"],
        )
        lookup[title_field] = self.TARGET_PROFILE["role_title"]

        profile, _created = TargetRoleProfile.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        return profile

    def _upsert_application(self, owner, application_data, days_ago):
        """Create or update a deterministic demo job application."""
        applied_date = timezone.localdate() - timedelta(days=days_ago)

        defaults = self._model_defaults(
            JobApplication,
            {
                "title": application_data["title"],
                "company": application_data["company"],
                "status": application_data["status"],
                "job_link": application_data["job_link"],
                "job_description": application_data["job_description"],
                "description": application_data["job_description"],
                "notes": application_data["notes"],
                "applied_date": applied_date,
            },
        )

        lookup = self._owner_lookup(JobApplication, owner)
        lookup["company"] = application_data["company"]
        lookup["title"] = application_data["title"]

        application, _created = JobApplication.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        return application

    def _upsert_note(self, application, note_body):
        """Create a deterministic note for a demo application."""
        defaults = self._model_defaults(
            ApplicationNote,
            {
                "body": note_body,
                "content": note_body,
                "note": note_body,
            },
        )

        body_field = self._first_existing_field(ApplicationNote, ["body", "content", "note"])
        lookup = {
            "application": application,
            body_field: note_body,
        }

        ApplicationNote.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )

    def _upsert_insight(self, application, target_profile):
        """Create or update a deterministic sample insight for the application."""
        extracted_keywords = [
            "python",
            "django",
            "api",
            "postgresql",
            "docker",
            "testing",
        ]
        matched_keywords = ["python", "django", "api", "postgresql", "docker"]
        missing_keywords = ["ci"]

        defaults = self._model_defaults(
            JobInsight,
            {
                "target_profile": target_profile,
                "extracted_keywords": extracted_keywords,
                "matched_keywords": matched_keywords,
                "missing_keywords": missing_keywords,
                "similarity_score": 0.83,
                "score": 0.83,
                "source_text_hash": f"demo-{application.pk}",
                "explanation": (
                    "This demo role strongly matches the target profile because "
                    "it includes Python, Django, API, PostgreSQL, Docker, and "
                    "testing language."
                ),
            },
        )

        lookup = {"job_application": application}
        if self._has_field(JobInsight, "target_profile"):
            lookup["target_profile"] = target_profile

        JobInsight.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )

    def _owner_lookup(self, model_class, owner):
        """Return the correct owner lookup for a model."""
        if self._has_field(model_class, "owner"):
            return {"owner": owner}
        if self._has_field(model_class, "user"):
            return {"user": owner}
        raise ValueError(f"{model_class.__name__} must define owner or user.")

    def _model_defaults(self, model_class, values):
        """Filter default values to fields that exist on a model."""
        return {
            field_name: value
            for field_name, value in values.items()
            if self._has_field(model_class, field_name)
        }

    def _first_existing_field(self, model_class, field_names):
        """Return the first field name that exists on a model."""
        for field_name in field_names:
            if self._has_field(model_class, field_name):
                return field_name
        raise ValueError(
            f"{model_class.__name__} must define one of: {', '.join(field_names)}."
        )

    def _has_field(self, model_class, field_name):
        """Return whether a model has the named field."""
        return any(field.name == field_name for field in model_class._meta.fields)
