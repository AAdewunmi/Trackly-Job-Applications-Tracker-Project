"""URL routes for Trackly job application API endpoints."""

from django.urls import path

from apps.jobs.api.views import (
    ApplicationNoteListCreateAPIView,
    JobApplicationDetailAPIView,
    JobApplicationListCreateAPIView,
)

urlpatterns = [
    path(
        "applications/",
        JobApplicationListCreateAPIView.as_view(),
        name="job-application-list-create",
    ),
    path(
        "applications/<int:pk>/",
        JobApplicationDetailAPIView.as_view(),
        name="job-application-detail",
    ),
    path(
        "applications/<int:application_pk>/notes/",
        ApplicationNoteListCreateAPIView.as_view(),
        name="application-note-list-create",
    ),
]
