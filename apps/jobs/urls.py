"""URL routes for Trackly job application workflows."""

from django.urls import path

from apps.jobs.views import (
    JobApplicationDetailView,
    application_create,
    application_delete,
    application_list,
    application_update,
)

app_name = "jobs"

urlpatterns = [
    path("applications/", application_list, name="application_list"),
    path("applications/new/", application_create, name="application_create"),
    path(
        "applications/<int:pk>/",
        JobApplicationDetailView.as_view(),
        name="application_detail",
    ),
    path("applications/<int:pk>/edit/", application_update, name="application_update"),
    path(
        "applications/<int:pk>/delete/",
        application_delete,
        name="application_delete",
    ),
]
