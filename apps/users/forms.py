"""Forms for Trackly authentication and account workflows."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.users.models import User


class SignUpForm(UserCreationForm):
    """Create a new Trackly user account from the public signup page."""

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta:
        """Form metadata for user signup."""

        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def clean_email(self) -> str:
        """Validate that the email address is not already registered."""
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")

        return email


class EmailAuthenticationForm(AuthenticationForm):
    """Authenticate users with an email-labelled username field."""

    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )
