"""Views for Trackly signup, login, logout, and profile workflows."""

from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView

from apps.roles.permissions import is_trackly_admin
from apps.users.forms import EmailAuthenticationForm, SignUpForm


class SignUpView(CreateView):
    """Register a new user and sign them into Trackly."""

    form_class = SignUpForm
    template_name = "users/signup.html"
    success_url = reverse_lazy("dashboard:user")

    def form_valid(self, form: SignUpForm) -> HttpResponse:
        """Persist the new user, authenticate them, and redirect to dashboard."""
        self.object = form.save()
        login(self.request, self.object)
        messages.success(self.request, "Your Trackly account has been created.")
        return redirect(self.get_success_url())


class TracklyLoginView(LoginView):
    """Authenticate an existing Trackly user."""

    authentication_form = EmailAuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        """Redirect admins to admin surface and standard users to user dashboard."""
        if is_trackly_admin(self.request.user):
            return reverse("dashboard:admin")

        return super().get_success_url()

    def form_valid(self, form: EmailAuthenticationForm) -> HttpResponse:
        """Show a friendly success message after login."""
        messages.success(self.request, "You are signed in.")
        return super().form_valid(form)


class TracklyLogoutView(LogoutView):
    """Sign the current user out of Trackly."""

    next_page = reverse_lazy("users:login")

    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """Add a logout message before the session is cleared."""
        if request.user.is_authenticated:
            messages.info(request, "You have signed out.")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    """Display the authenticated user's account profile."""

    template_name = "users/profile.html"
