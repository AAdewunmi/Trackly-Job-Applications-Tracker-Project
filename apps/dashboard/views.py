"""Dashboard views for Trackly product surfaces."""

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from apps.roles.models import Role
from apps.roles.permissions import is_trackly_admin


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """Display the authenticated user's Trackly dashboard shell."""

    template_name = "dashboard/user_index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Add Sprint 1 empty-state dashboard context."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Dashboard"
        return context


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Display the protected admin dashboard shell."""

    template_name = "dashboard/admin_index.html"
    raise_exception = True

    def test_func(self) -> bool:
        """Allow staff users or users with the active admin role."""
        return is_trackly_admin(self.request.user)

    def handle_no_permission(self):
        """Return login redirects for anonymous users and 403 for wrong roles."""
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        raise PermissionDenied("You do not have permission to access this dashboard.")

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Add initial admin overview counts."""
        context = super().get_context_data(**kwargs)
        user_model = get_user_model()

        context["page_title"] = "Admin Dashboard"
        context["total_users"] = user_model.objects.count()
        context["total_roles"] = Role.objects.count()
        return context
