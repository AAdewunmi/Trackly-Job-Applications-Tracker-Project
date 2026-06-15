"""Tests for deterministic Trackly demo data seeding."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.insights.models import JobInsight
from apps.insights.models import TargetRoleProfile
from apps.jobs.models import ApplicationNote
from apps.jobs.models import JobApplication
from apps.roles.models import Role


@pytest.mark.django_db
def test_seed_roles_creates_required_roles():
    """seed_roles creates the baseline admin and user roles."""
    call_command("seed_roles")

    assert Role.objects.filter(slug="admin").exists()
    assert Role.objects.filter(slug="user").exists()


@pytest.mark.django_db
def test_seed_demo_data_creates_demo_records():
    """seed_demo_data creates demo users and product records."""
    call_command("seed_demo_data")

    User = get_user_model()

    assert User.objects.filter(email="admin.demo@trackly.local").exists()
    assert User.objects.filter(email="user.demo@trackly.local").exists()
    assert JobApplication.objects.count() == 3
    assert ApplicationNote.objects.count() == 3
    assert TargetRoleProfile.objects.count() == 1
    assert JobInsight.objects.count() == 3


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent():
    """Running seed_demo_data twice must not duplicate deterministic records."""
    call_command("seed_demo_data")
    call_command("seed_demo_data")

    User = get_user_model()

    assert User.objects.filter(email__endswith="@trackly.local").count() == 2
    assert Role.objects.filter(slug__in=["admin", "user"]).count() == 2
    assert JobApplication.objects.count() == 3
    assert ApplicationNote.objects.count() == 3
    assert TargetRoleProfile.objects.count() == 1
    assert JobInsight.objects.count() == 3