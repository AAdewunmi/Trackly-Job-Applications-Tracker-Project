"""
Browser views for Trackly insight workflows.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from apps.insights.forms import JobInsightGenerationForm, TargetRoleProfileForm
from apps.insights.selectors import (
    get_recent_insights_for_user,
    get_target_profiles_for_user,
)
from apps.insights.services import generate_job_insight
from apps.jobs.models import JobApplication


class InsightListView(LoginRequiredMixin, TemplateView):
    """Show recent insights and target profiles for the logged-in user."""

    template_name = "insights/insight_list.html"

    def get_context_data(self, **kwargs):
        """Add user-scoped insight dashboard data."""
        context = super().get_context_data(**kwargs)
        context["recent_insights"] = get_recent_insights_for_user(self.request.user)
        context["target_profiles"] = get_target_profiles_for_user(self.request.user)
        return context


class TargetRoleProfileCreateView(LoginRequiredMixin, CreateView):
    """Create a target role profile for the logged-in user."""

    form_class = TargetRoleProfileForm
    template_name = "insights/target_profile_form.html"
    success_url = reverse_lazy("insights:insight-list")

    def form_valid(self, form):
        """Assign target profile ownership before saving."""
        form.instance.owner = self.request.user
        messages.success(self.request, "Target role profile created.")
        return super().form_valid(form)


class GenerateJobInsightView(LoginRequiredMixin, View):
    """Generate a stored insight from an application detail page."""

    def post(self, request, application_pk: int):
        """Generate or reuse an insight and redirect to the application detail page."""
        application = get_object_or_404(
            JobApplication,
            pk=application_pk,
            owner=request.user,
        )
        form = JobInsightGenerationForm(request.POST, user=request.user)

        if not form.is_valid():
            messages.error(request, "Select a target role profile before generating.")
            return redirect("jobs:application-detail", pk=application.pk)

        try:
            result = generate_job_insight(
                user=request.user,
                application=application,
                target_profile=form.cleaned_data["target_profile"],
            )
        except PermissionDenied:
            messages.error(request, "You cannot generate this insight.")
            return redirect("jobs:application-detail", pk=application.pk)

        if result.created:
            messages.success(request, "Job insight generated.")
        else:
            messages.info(request, "Existing insight reused for unchanged content.")

        return redirect("jobs:application-detail", pk=application.pk)
