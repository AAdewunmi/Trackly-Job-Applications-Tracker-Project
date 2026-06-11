"""
Forms for Trackly target role and insight generation workflows.
"""

from django import forms

from apps.insights.models import TargetRoleProfile


class TargetRoleProfileForm(forms.ModelForm):
    """Form used to create a target role profile."""

    keywords_text = forms.CharField(
        label="Target keywords",
        help_text="Enter comma-separated skills, tools, or role keywords.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    class Meta:
        """Form metadata for target role profiles."""

        model = TargetRoleProfile
        fields = ["title", "description", "keywords_text", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        """Initialise the form with stored JSON keywords as comma-separated text."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["keywords_text"].initial = ", ".join(self.instance.keywords)

    def clean_keywords_text(self) -> list[str]:
        """Convert comma-separated keyword text into a cleaned keyword list."""
        raw_keywords = self.cleaned_data["keywords_text"]
        keywords = [
            keyword.strip().lower()
            for keyword in raw_keywords.split(",")
            if keyword.strip()
        ]

        if not keywords:
            raise forms.ValidationError("At least one target keyword is required.")

        return keywords

    def save(self, commit: bool = True):
        """Save the target role profile with JSON-backed keywords."""
        instance = super().save(commit=False)
        instance.keywords = self.cleaned_data["keywords_text"]

        if commit:
            instance.save()

        return instance


class JobInsightGenerationForm(forms.Form):
    """Form used to select a target profile for insight generation."""

    target_profile = forms.ModelChoiceField(
        queryset=TargetRoleProfile.objects.none(),
        label="Target role profile",
    )

    def __init__(self, *args, user, **kwargs):
        """Limit target profile choices to the logged-in user."""
        super().__init__(*args, **kwargs)
        self.fields["target_profile"].queryset = TargetRoleProfile.objects.filter(
            owner=user,
            is_active=True,
        ).order_by("title")
