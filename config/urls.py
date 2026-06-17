"""
Root URL configuration for Trackly.

The project exposes browser-based product routes and versioned API routes from
one central URL module.
"""

import os
from datetime import UTC, datetime

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.views import home


def health_check(request):
    """Return a lightweight operational health response for deployment checks."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "trackly",
            "release": os.environ.get("RELEASE_VERSION", "local"),
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
    )


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("accounts/", include("apps.users.urls")),
    path("applications/", include("apps.jobs.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("insights/", include("apps.insights.urls")),
    path("api/v1/jobs/", include("apps.jobs.api.urls")),
    path("api/v1/insights/", include("apps.insights.api.urls")),
    path(
        "api/v1/auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
