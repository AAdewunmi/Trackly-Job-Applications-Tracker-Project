"""URL routes for Trackly job application workflows."""

from django.urls import path

from apps.jobs.views import JobApplicationDetailView

app_name = "jobs"

urlpatterns = [
    path(
        "applications/<int:pk>/",
        JobApplicationDetailView.as_view(),
        name="application_detail",
    ),
]
