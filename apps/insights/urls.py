"""
URL routes for Trackly insight browser workflows.
"""

from django.urls import path

from apps.insights.views import (
    GenerateJobInsightView,
    InsightListView,
    TargetRoleProfileCreateView,
)

app_name = "insights"

urlpatterns = [
    path("", InsightListView.as_view(), name="insight-list"),
    path(
        "target-profiles/new/",
        TargetRoleProfileCreateView.as_view(),
        name="target-profile-create",
    ),
    path(
        "applications/<int:application_pk>/generate/",
        GenerateJobInsightView.as_view(),
        name="job-insight-generate",
    ),
]
