"""
Serializers for Trackly job application API resources.
"""

from rest_framework import serializers

from apps.jobs.models import JobApplication


class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for user-owned job applications."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        """Serializer metadata for the job application API contract."""

        model = JobApplication
        fields = [
            "id",
            "owner_email",
            "title",
            "company",
            "status",
            "job_link",
            "applied_date",
            "job_description",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner_email", "created_at", "updated_at"]