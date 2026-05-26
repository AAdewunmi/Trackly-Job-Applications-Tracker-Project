"""URL routes for Trackly user account workflows."""

from django.urls import path

from apps.users.views import (
    ProfileView,
    SignUpView,
    TracklyLoginView,
    TracklyLogoutView,
)

app_name = "users"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", TracklyLoginView.as_view(), name="login"),
    path("logout/", TracklyLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
