"""
API views for Trackly insight generation and reading.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.insights.api.serializers import (
    GenerateJobInsightSerializer,
    JobInsightSerializer,
)
from apps.insights.models import TargetRoleProfile
from apps.insights.selectors import get_insights_for_user
from apps.insights.services import generate_job_insight
from apps.jobs.models import JobApplication


class JobInsightListAPIView(APIView):
    """List stored insights owned by the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return stored insights for the current user."""
        serializer = JobInsightSerializer(
            get_insights_for_user(request.user),
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class GenerateJobInsightAPIView(APIView):
    """Generate or reuse a job insight for a user-owned application."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate an insight through the secured API."""
        serializer = GenerateJobInsightSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = get_object_or_404(
            JobApplication,
            pk=serializer.validated_data["job_application_id"],
            owner=request.user,
        )
        target_profile = get_object_or_404(
            TargetRoleProfile,
            pk=serializer.validated_data["target_profile_id"],
            owner=request.user,
            is_active=True,
        )

        result = generate_job_insight(
            user=request.user,
            application=application,
            target_profile=target_profile,
        )

        response_status = (
            status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
        )
        return Response(
            {
                "created": result.created,
                "insight": JobInsightSerializer(result.insight).data,
            },
            status=response_status,
        )
