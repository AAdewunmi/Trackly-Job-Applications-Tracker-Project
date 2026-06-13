"""
Serialisers for Trackly insight API endpoints.
"""

from rest_framework import serializers

from apps.insights.models import JobInsight


class JobInsightSerializer(serializers.ModelSerializer):
    """Serializer for stored job insight output."""

    job_application_title = serializers.CharField(
        source="job_application.title",
        read_only=True,
    )
    target_profile_title = serializers.CharField(
        source="target_profile.title",
        read_only=True,
    )

    class Meta:
        """Serializer metadata for stored job insights."""

        model = JobInsight
        fields = [
            "id",
            "job_application",
            "job_application_title",
            "target_profile",
            "target_profile_title",
            "source_hash",
            "pipeline_version",
            "extracted_terms",
            "top_overlapping_terms",
            "top_overlapping_weighted_terms",
            "missing_target_terms",
            "missing_weighted_target_terms",
            "similarity_score",
            "score_label",
            "explanation",
            "created_at",
        ]
        read_only_fields = fields


class GenerateJobInsightSerializer(serializers.Serializer):
    """Input serializer for API-driven insight generation."""

    job_application_id = serializers.IntegerField()
    target_profile_id = serializers.IntegerField()
