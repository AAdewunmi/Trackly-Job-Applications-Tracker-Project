"""Management command for seeding Trackly role records."""

from django.core.management.base import BaseCommand

from apps.roles.models import Role


class Command(BaseCommand):
    """Seed the baseline roles required by the Trackly product surfaces."""

    help = "Seed deterministic Trackly roles."

    DEFAULT_ROLES = [
        {
            "slug": "admin",
            "name": "Admin",
            "description": "Can access administrative product surfaces.",
        },
        {
            "slug": "user",
            "name": "User",
            "description": "Can manage personal job applications and insights.",
        },
    ]

    def handle(self, *args, **options):
        """Create or update baseline role records without producing duplicates."""
        created_count = 0
        updated_count = 0

        for role_data in self.DEFAULT_ROLES:
            role, created = Role.objects.update_or_create(
                slug=role_data["slug"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"],
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.slug}"))
            else:
                updated_count += 1
                self.stdout.write(f"Updated role: {role.slug}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded roles successfully. Created={created_count}, "
                f"Updated={updated_count}."
            )
        )
