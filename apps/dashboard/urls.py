"""URL routes for Trackly dashboards."""

from django.urls import path

from apps.dashboard.views import AdminDashboardView, UserDashboardView

app_name = "dashboard"

urlpatterns = [
    path("", UserDashboardView.as_view(), name="user"),
    path("admin/", AdminDashboardView.as_view(), name="admin"),
]
