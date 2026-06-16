"""Tests for deterministic Trackly demo data seeding."""

from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import ApplicationNote, JobApplication
from apps.roles.models import Role

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_seed_commands_makefile_and_docs_are_present():
    """Seed setup is exposed through commands, Make targets, and reviewer docs."""
    seed_roles_command = PROJECT_ROOT / "apps/roles/management/commands/seed_roles.py"
    seed_demo_command = PROJECT_ROOT / "apps/jobs/management/commands/seed_demo_data.py"
    makefile = (PROJECT_ROOT / "Makefile").read_text()
    readme = (PROJECT_ROOT / "README.md").read_text()
    local_setup = (PROJECT_ROOT / "docs/local-setup.md").read_text()

    assert seed_roles_command.exists()
    assert seed_demo_command.exists()
    assert "Seed deterministic Trackly roles." in seed_roles_command.read_text()
    assert "Seed repeatable demo data for Trackly." in seed_demo_command.read_text()
    assert "seed:" in makefile
    assert "$(MANAGE_T) seed_demo_data" in makefile
    assert "loaddata:" in makefile
    assert "$(MANAGE_T) loaddata $(FIXTURE)" in makefile
    assert "make seed" in readme
    assert "make loaddata FIXTURE=path/to/fixture.json" in readme
    assert "make seed" in local_setup
    assert "make loaddata FIXTURE=path/to/fixture.json" in local_setup


@pytest.mark.django_db
def test_seed_roles_creates_required_roles_without_duplicates():
    """seed_roles creates and updates baseline roles without duplicates."""
    call_command("seed_roles")
    call_command("seed_roles")

    assert Role.objects.filter(code=Role.Codes.ADMIN).count() == 1
    assert Role.objects.filter(code=Role.Codes.MEMBER).count() == 1
    assert Role.objects.get(code=Role.Codes.ADMIN).name == "Admin"
    assert Role.objects.get(code=Role.Codes.MEMBER).name == "Member"


@pytest.mark.django_db
def test_seed_demo_data_creates_demo_records():
    """seed_demo_data creates demo users and product records for walkthroughs."""
    call_command("seed_demo_data")

    User = get_user_model()

    admin = User.objects.get(email="admin.demo@trackly.local")
    member = User.objects.get(email="user.demo@trackly.local")
    analyst = User.objects.get(email="analyst.demo@trackly.local")
    empty_state_user = User.objects.get(email="empty.demo@trackly.local")

    assert admin.check_password("TracklyDemoPass123")
    assert member.check_password("TracklyDemoPass123")
    assert analyst.check_password("TracklyDemoPass123")
    assert empty_state_user.check_password("TracklyDemoPass123")
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.roles.filter(code=Role.Codes.ADMIN).exists()
    assert member.roles.filter(code=Role.Codes.MEMBER).exists()
    assert analyst.roles.filter(code=Role.Codes.MEMBER).exists()
    assert empty_state_user.roles.filter(code=Role.Codes.MEMBER).exists()

    assert JobApplication.objects.count() == 10
    assert ApplicationNote.objects.count() == 10
    assert TargetRoleProfile.objects.count() == 4
    assert JobInsight.objects.count() == 10
    assert set(JobApplication.objects.values_list("status", flat=True)) == {
        JobApplication.Status.APPLIED,
        JobApplication.Status.INTERVIEWING,
        JobApplication.Status.SAVED,
        JobApplication.Status.SCREENING,
        JobApplication.Status.OFFER,
        JobApplication.Status.REJECTED,
        JobApplication.Status.WITHDRAWN,
    }
    assert member.job_applications.count() == 8
    assert analyst.job_applications.count() == 2
    assert empty_state_user.job_applications.count() == 0
    assert empty_state_user.target_role_profiles.count() == 0

    expected_dates = {
        timezone.localdate() - timedelta(days=offset) for offset in range(10)
    }
    assert set(JobApplication.objects.values_list("applied_date", flat=True)) == (
        expected_dates
    )

    backend_profile = TargetRoleProfile.objects.get(
        owner=member,
        title="Backend Engineer",
    )
    assert backend_profile.keywords == [
        "python",
        "django",
        "postgresql",
        "docker",
        "api",
        "testing",
        "ci",
        "backend",
    ]

    offer = JobApplication.objects.get(owner=member, company="BrightPath")
    assert offer.status == JobApplication.Status.OFFER
    assert offer.application_notes.filter(
        body__icontains="Compare salary, learning scope, and mentorship."
    ).exists()
    insight = JobInsight.objects.get(
        job_application=offer,
        target_profile=backend_profile,
    )
    assert insight.pipeline_version == JobInsight.PipelineVersion.NLTK_TFIDF_COSINE_V1
    assert 0 <= insight.similarity_score <= 1
    assert insight.score_label
    assert insight.explanation
    assert insight.extracted_terms


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent():
    """Running seed_demo_data twice must not duplicate seeded records."""
    call_command("seed_demo_data")
    call_command("seed_demo_data")

    User = get_user_model()

    assert User.objects.filter(email__endswith="@trackly.local").count() == 4
    assert (
        Role.objects.filter(code__in=[Role.Codes.ADMIN, Role.Codes.MEMBER]).count() == 2
    )
    assert JobApplication.objects.count() == 10
    assert ApplicationNote.objects.count() == 10
    assert TargetRoleProfile.objects.count() == 4
    assert JobInsight.objects.count() == 10
    assert (
        JobApplication.objects.values("owner", "company", "title").distinct().count()
        == 10
    )
    assert TargetRoleProfile.objects.values("owner", "title").distinct().count() == 4
    assert (
        ApplicationNote.objects.values("application", "body").distinct().count() == 10
    )
    assert (
        JobInsight.objects.values(
            "job_application",
            "target_profile",
            "source_hash",
            "pipeline_version",
        )
        .distinct()
        .count()
        == 10
    )


@pytest.mark.django_db
def test_seed_demo_data_resets_stale_demo_records():
    """Reruns reset seeded demo-member data to the deterministic walkthrough set."""
    call_command("seed_demo_data")

    User = get_user_model()
    member = User.objects.get(email="user.demo@trackly.local")

    JobApplication.objects.create(
        owner=member,
        title="Old Manual Demo Job",
        company="Outdated Co",
        status=JobApplication.Status.SAVED,
        applied_date=timezone.localdate(),
    )
    TargetRoleProfile.objects.create(
        owner=member,
        title="Old Manual Profile",
        keywords=["legacy"],
    )

    assert JobApplication.objects.count() == 11
    assert TargetRoleProfile.objects.count() == 5

    call_command("seed_demo_data")

    assert not JobApplication.objects.filter(
        owner=member,
        title="Old Manual Demo Job",
        company="Outdated Co",
    ).exists()
    assert not TargetRoleProfile.objects.filter(
        owner=member,
        title="Old Manual Profile",
    ).exists()
    assert JobApplication.objects.count() == 10
    assert TargetRoleProfile.objects.count() == 4


@pytest.mark.django_db
def test_seed_demo_data_outputs_demo_credentials_and_record_count():
    """Command output gives reviewers enough information to verify without setup."""
    from io import StringIO

    stdout = StringIO()

    call_command("seed_demo_data", stdout=stdout)

    output = stdout.getvalue()
    assert "Trackly demo data seeded successfully." in output
    assert "admin.demo@trackly.local / TracklyDemoPass123" in output
    assert "user.demo@trackly.local / TracklyDemoPass123" in output
    assert "analyst.demo@trackly.local / TracklyDemoPass123" in output
    assert "empty.demo@trackly.local / TracklyDemoPass123" in output
    assert "Demo applications available: 10" in output
