"""Views for Trackly job application workflows."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import DetailView

from apps.jobs.models import JobApplication


class JobApplicationDetailView(LoginRequiredMixin, DetailView):
    """Display a single job application owned by the authenticated user."""

    model = JobApplication
    template_name = "jobs/application_detail.html"
    context_object_name = "application"

    def get_queryset(self) -> QuerySet[JobApplication]:
        """Limit detail lookups to applications owned by the current user."""
        return JobApplication.objects.filter(owner=self.request.user)
