"""Views for Trackly job application workflows."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.insights.forms import JobInsightGenerationForm
from apps.insights.selectors import get_latest_insight_for_application
from apps.jobs.forms import ApplicationNoteForm, JobApplicationForm
from apps.jobs.models import JobApplication
from apps.jobs.selectors import (
    application_queryset_for_user,
    get_user_application_or_404,
    get_user_note_or_404,
)


@login_required
def application_list(request: HttpRequest) -> HttpResponse:
    """Render the authenticated user's job application list."""
    applications = application_queryset_for_user(request.user)

    return render(
        request,
        "jobs/application_list.html",
        {
            "applications": applications,
        },
    )


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
            "insight_generation_form": JobInsightGenerationForm(user=request.user),
            "latest_insight": get_latest_insight_for_application(application),
            "note_form": note_form,
            "notes": application.application_notes.all(),
        },
    )


@login_required
def application_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Update an existing user-owned job application."""
    application = get_user_application_or_404(request.user, pk=pk)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, instance=application)

        if form.is_valid():
            updated_application = form.save()

            messages.success(request, "Application updated successfully.")
            return redirect(updated_application.get_absolute_url())

        messages.error(request, "Please correct the errors below.")
    else:
        form = JobApplicationForm(instance=application)

    return render(
        request,
        "jobs/application_form.html",
        {
            "form": form,
            "application": application,
            "form_title": "Edit job application",
            "submit_label": "Save changes",
        },
    )


@login_required
def application_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a user-owned job application after confirmation."""
    application = get_user_application_or_404(request.user, pk=pk)

    if request.method == "POST":
        application.delete()

        messages.success(request, "Application deleted successfully.")
        return redirect("jobs:application_list")

    return render(
        request,
        "jobs/application_confirm_delete.html",
        {
            "application": application,
        },
    )


@login_required
def note_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Update a note attached to one of the authenticated user's applications."""
    note = get_user_note_or_404(request.user, pk=pk)

    if request.method == "POST":
        form = ApplicationNoteForm(request.POST, instance=note)

        if form.is_valid():
            updated_note = form.save()

            messages.success(request, "Note updated successfully.")
            return redirect(updated_note.application.get_absolute_url())

        messages.error(request, "Please correct the note errors below.")
    else:
        form = ApplicationNoteForm(instance=note)

    return render(
        request,
        "jobs/note_form.html",
        {
            "application": note.application,
            "form": form,
            "note": note,
        },
    )


@login_required
def note_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a note attached to one of the authenticated user's applications."""
    note = get_user_note_or_404(request.user, pk=pk)
    application = note.application

    if request.method == "POST":
        note.delete()

        messages.success(request, "Note deleted successfully.")
        return redirect(application.get_absolute_url())

    return render(
        request,
        "jobs/note_confirm_delete.html",
        {
            "application": application,
            "note": note,
        },
    )
