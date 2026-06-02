"""URL routes for Trackly dashboards."""

from django.urls import path

from apps.dashboard.views import admin_index, user_index, user_preview

app_name = "dashboard"

urlpatterns = [
    path("", user_index, name="user"),
    path("preview/", user_preview, name="user-preview"),
    path("admin/", admin_index, name="admin"),
]
