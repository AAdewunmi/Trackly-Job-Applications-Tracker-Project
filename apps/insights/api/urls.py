"""
URL routes for Trackly insight API endpoints.
"""

from django.urls import path

from apps.insights.api.views import GenerateJobInsightAPIView, JobInsightListAPIView


urlpatterns = [
    path("", JobInsightListAPIView.as_view(), name="job-insight-list"),
    path(
        "generate/",
        GenerateJobInsightAPIView.as_view(),
        name="job-insight-generate",
    ),
]
