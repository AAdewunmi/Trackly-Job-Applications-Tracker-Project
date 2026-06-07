"""Forms for Trackly job application workflows."""

from django import forms

from apps.jobs.models import ApplicationNote, JobApplication


class JobApplicationForm(forms.ModelForm):
    """Form for creating and updating user-owned job applications."""

    job_link = forms.URLField(
        assume_scheme="https",
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://company.example/jobs/123",
            }
        ),
    )

    class Meta:
        """Form metadata for editable job application fields."""

        model = JobApplication
        fields = [
            "title",
            "company",
            "status",
            "job_link",
            "applied_date",
            "job_description",
            "notes",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Backend Engineer",
                }
            ),
            "company": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Acme Ltd",
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "applied_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "job_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": "Paste the job description or role summary.",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Initial notes about the role.",
                }
            ),
        }

    def clean_title(self) -> str:
        """Return a normalised application title."""
        return self.cleaned_data["title"].strip()

    def clean_company(self) -> str:
        """Return a normalised company name."""
        return self.cleaned_data["company"].strip()


class ApplicationNoteForm(forms.ModelForm):
    """Form for adding a note to an existing application."""

    class Meta:
        """Form metadata for application note entry."""

        model = ApplicationNote
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Add a recruiter update, interview note, or follow-up."
                    ),
                }
            )
        }
        labels = {
            "body": "New note",
        }
        error_messages = {
            "body": {
                "required": "Note body is required.",
            },
        }

    def clean_body(self) -> str:
        """Return normalised note content."""
        return self.cleaned_data["body"].strip()
