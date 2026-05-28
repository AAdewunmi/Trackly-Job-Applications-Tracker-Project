"""Root URL configuration for Trackly."""

from django.contrib import admin
from django.urls import include, path

from config.views import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.users.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("jobs/", include("apps.jobs.urls")),
]
