"""Views for Trackly job application workflows."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.jobs.forms import ApplicationNoteForm, JobApplicationForm
from apps.jobs.models import JobApplication


def application_queryset_for_user(user) -> QuerySet[JobApplication]:
    """Return job applications owned by the provided user."""
    return JobApplication.objects.filter(owner=user)


def get_user_application_or_404(user, pk: int) -> JobApplication:
    """Return a user-owned application or raise a 404."""
    return get_object_or_404(application_queryset_for_user(user), pk=pk)


@login_required
def application_create(request: HttpRequest) -> HttpResponse:
    """Create a new job application owned by the authenticated user."""
    if request.method == "POST":
        form = JobApplicationForm(request.POST)

        if form.is_valid():
            application = form.save(commit=False)
            application.owner = request.user
            application.save()

            messages.success(request, "Application created successfully.")
            return redirect(application.get_absolute_url())

        messages.error(request, "Please correct the errors below.")
    else:
        form = JobApplicationForm(
            initial={
                "status": JobApplication.Status.SAVED,
            }
        )

    return render(
        request,
        "jobs/application_form.html",
        {
            "form": form,
            "form_title": "Add job application",
            "submit_label": "Create application",
        },
    )


@login_required
def application_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Render a user-owned application and handle inline note creation."""
    application = get_user_application_or_404(request.user, pk=pk)

    if request.method == "POST":
        note_form = ApplicationNoteForm(request.POST)

        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.application = application
            note.save()

            messages.success(request, "Note added successfully.")
            return redirect(application.get_absolute_url())

        messages.error(request, "Please correct the note errors below.")
    else:
        note_form = ApplicationNoteForm()

    return render(
        request,
        "jobs/application_detail.html",
        {
            "application": application,
            "note_form": note_form,
            "notes": application.application_notes.all(),
        },
    )


class JobApplicationDetailView(LoginRequiredMixin, View):
    """Compatibility wrapper for the existing detail URLconf."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Render the detail view for GET requests."""
        return application_detail(request, pk=pk)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Handle inline note creation for POST requests."""
        return application_detail(request, pk=pk)
