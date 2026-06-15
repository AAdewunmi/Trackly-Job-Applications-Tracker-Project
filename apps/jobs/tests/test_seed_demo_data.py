"""Tests for deterministic Trackly demo data seeding."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.insights.models import JobInsight, TargetRoleProfile
from apps.jobs.models import ApplicationNote, JobApplication
from apps.roles.models import Role


@pytest.mark.django_db
def test_seed_roles_creates_required_roles():
    """seed_roles creates the baseline admin and member roles."""
    call_command("seed_roles")

    assert Role.objects.filter(code=Role.Codes.ADMIN).exists()
    assert Role.objects.filter(code=Role.Codes.MEMBER).exists()


@pytest.mark.django_db
def test_seed_demo_data_creates_demo_records():
    """seed_demo_data creates demo users and product records."""
    call_command("seed_demo_data")

    User = get_user_model()

    assert User.objects.filter(email="admin.demo@trackly.local").exists()
    assert User.objects.filter(email="user.demo@trackly.local").exists()
    assert User.objects.filter(email="analyst.demo@trackly.local").exists()
    assert User.objects.filter(email="empty.demo@trackly.local").exists()
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


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent():
    """Running seed_demo_data twice must not duplicate deterministic records."""
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
