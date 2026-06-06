"""URL routes for Trackly dashboards."""

from django.urls import path

from apps.dashboard.views import admin_index, user_index

app_name = "dashboard"

urlpatterns = [
    path("", user_index, name="user"),
    path("admin/", admin_index, name="admin"),
]
