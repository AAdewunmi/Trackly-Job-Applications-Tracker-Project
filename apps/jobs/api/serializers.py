"""Serializers for Trackly job application API resources."""

from rest_framework import serializers

from apps.jobs.models import ApplicationNote, JobApplication


class ApplicationNoteSerializer(serializers.ModelSerializer):
    """Serializer for notes attached to user-owned applications."""

    class Meta:
        """Serializer metadata for application notes."""

        model = ApplicationNote
        fields = [
            "id",
            "body",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_body(self, value: str) -> str:
        """Return normalised note content."""
        body = value.strip()

        if not body:
            raise serializers.ValidationError("Note body is required.")

        return body


class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for user-owned job applications."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    application_notes = ApplicationNoteSerializer(many=True, read_only=True)

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
            "application_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner_email",
            "application_notes",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value: str) -> str:
        """Return a normalised application title."""
        title = value.strip()

        if not title:
            raise serializers.ValidationError("Application title is required.")

        return title

    def validate_company(self, value: str) -> str:
        """Return a normalised company name."""
        company = value.strip()

        if not company:
            raise serializers.ValidationError("Company name is required.")

        return company
