# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults
from django.views import static as static_views

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


API_BASE_URL = 'api/v1/'

urlpatterns = []

# If static files are not intercepted by the web-server, serve them with the dev-server:
if settings.DEBUG is False:  # if DEBUG is True it will be served automatically
    urlpatterns += [
        path(
            'static/<path>',
            static_views.serve,
            {'document_root': settings.STATIC_ROOT}
            ),
        ]

api_urls = [
    path(
        '{}'.format(API_BASE_URL),
        include("osmchadjango.changeset.urls", namespace="changeset")
        ),
    path(
        '{}'.format(API_BASE_URL),
        include("osmchadjango.supervise.urls", namespace="supervise")
        ),
    path(
        '{}'.format(API_BASE_URL),
        include("osmchadjango.users.urls", namespace="users")
        ),
    path(
        '{}'.format(API_BASE_URL),
        include("osmchadjango.roulette_integration.urls", namespace="challenge")
        ),
    ]

schema_view = get_schema_view(
    openapi.Info(
        title="OSMCha API",
        default_version='v1',
        description="OSMCha API Documentation",
        contact=openapi.Contact(email="osmcha-dev@openstreetmap.org"),
        license=openapi.License(name="Data © OpenStreetMap Contributors, ODBL license"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    # Django Admin
    path('admin/', admin.site.urls),

    # api docs
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
        ),
    re_path(
        r'^api-docs/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
        ),

    # include api_urls
    path(
        '',
        include(api_urls)
        ),

    # frontend urls
    path('', include("osmchadjango.frontend.urls", namespace="frontend")),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    import debug_toolbar
    urlpatterns += [
        path('400/', defaults.bad_request),
        path('403/', defaults.permission_denied),
        path('404/', defaults.page_not_found),
        path('500/', defaults.server_error),
        path('__debug__/', include(debug_toolbar.urls)),
        ]
