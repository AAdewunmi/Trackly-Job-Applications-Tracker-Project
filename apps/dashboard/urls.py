"""Dashboard URL routes."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.UserDashboardView.as_view(), name="user"),
    path("admin/", views.AdminDashboardView.as_view(), name="admin"),
]
