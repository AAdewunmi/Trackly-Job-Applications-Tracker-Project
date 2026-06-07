"""
API views for Trackly job application resources.
"""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.jobs.api.serializers import JobApplicationSerializer
from apps.jobs.models import JobApplication


class JobApplicationListCreateAPIView(generics.ListCreateAPIView):
    """List and create applications for the authenticated user."""

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only applications owned by the authenticated user."""
        return JobApplication.objects.filter(owner=self.request.user).order_by(
            "-updated_at",
            "-created_at",
        )

    def perform_create(self, serializer):
        """Assign ownership from the authenticated request."""
        serializer.save(owner=self.request.user)


class JobApplicationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete one user-owned application."""

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only applications owned by the authenticated user."""
        return JobApplication.objects.filter(owner=self.request.user)
