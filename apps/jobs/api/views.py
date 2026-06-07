"""API views for Trackly job application resources."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.jobs.api.serializers import (
    ApplicationNoteSerializer,
    JobApplicationSerializer,
)
from apps.jobs.selectors import (
    application_queryset_for_user,
    get_user_application_or_404,
    notes_queryset_for_user,
)


class JobApplicationListCreateAPIView(generics.ListCreateAPIView):
    """List and create applications for the authenticated user."""

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only applications owned by the authenticated user."""
        return application_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        """Assign ownership from the authenticated request."""
        serializer.save(owner=self.request.user)


class JobApplicationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete one user-owned application."""

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only applications owned by the authenticated user."""
        return application_queryset_for_user(self.request.user)


class ApplicationNoteListCreateAPIView(generics.ListCreateAPIView):
    """List and create notes for one authenticated user's application."""

    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsAuthenticated]

    def get_application(self):
        """Return the user-owned parent application."""
        return get_user_application_or_404(
            self.request.user,
            pk=self.kwargs["application_pk"],
        )

    def get_queryset(self):
        """Return notes attached to the user-owned parent application."""
        return self.get_application().application_notes.all()

    def perform_create(self, serializer):
        """Attach the note to the user-owned parent application."""
        serializer.save(application=self.get_application())


class ApplicationNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete one note on a user-owned application."""

    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return notes attached to the requested user-owned application."""
        application = get_user_application_or_404(
            self.request.user,
            pk=self.kwargs["application_pk"],
        )
        return notes_queryset_for_user(self.request.user).filter(
            application=application
        )
