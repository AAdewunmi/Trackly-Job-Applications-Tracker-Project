"""Factory helpers for user tests."""

import factory
from django.contrib.auth import get_user_model

from apps.roles.factories import RoleFactory


class UserFactory(factory.django.DjangoModelFactory):
    """Create a standard Trackly user for tests."""

    class Meta:
        """Factory metadata for UserFactory."""

        model = get_user_model()
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda number: f"user{number}@example.com")
    first_name = "Ada"
    last_name = "Lovelace"
    is_active = True

    @factory.post_generation
    def password(self, create: bool, extracted: str | None, **kwargs: object) -> None:
        """Set a usable password for generated users."""
        raw_password = extracted or "StrongPass12345!"
        self.set_password(raw_password)

        if create:
            self.save(update_fields=["password"])

    @factory.post_generation
    def roles(self, create: bool, extracted: list[object] | None, **kwargs: object) -> None:
        """Attach supplied roles to the generated user."""
        if not create:
            return

        if extracted:
            for role in extracted:
                self.roles.add(role)


class MemberUserFactory(UserFactory):
    """Create a Trackly user with the member role."""

    @factory.post_generation
    def roles(self, create: bool, extracted: list[object] | None, **kwargs: object) -> None:
        """Attach the member role unless specific roles are supplied."""
        if not create:
            return

        if extracted:
            for role in extracted:
                self.roles.add(role)
            return

        self.roles.add(RoleFactory())


class StaffUserFactory(UserFactory):
    """Create a Django staff user for admin-surface tests."""

    is_staff = True