"""URL routes for Trackly job application workflows."""

from django.urls import path

from apps.jobs import views

app_name = "jobs"

urlpatterns = [
    path("", views.application_list, name="application_list"),
    path("new/", views.application_create, name="application_create"),
    path("<int:pk>/", views.application_detail, name="application_detail"),
    path("<int:pk>/edit/", views.application_update, name="application_update"),
    path(
        "<int:pk>/delete/",
        views.application_delete,
        name="application_delete",
    ),
    path("notes/<int:pk>/edit/", views.note_update, name="note_update"),
    path("notes/<int:pk>/delete/", views.note_delete, name="note_delete"),
]
