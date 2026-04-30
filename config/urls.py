"""Root URL configuration for Trackly."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard:user", permanent=False)),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.users.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
]
