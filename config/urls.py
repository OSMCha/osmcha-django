# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults
from django.views import static as static_views

from .docs import SwaggerSchemaView

API_BASE_URL = 'api/v1/'

urlpatterns = []

# If static files are not intercepted by the web-server, serve them with the dev-server:
if settings.DEBUG is False:  # if DEBUG is True it will be served automatically
    urlpatterns += [
        path('static/<path>',
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
        include("osmchadjango.feature.urls", namespace="feature")
        ),
    path(
        '{}'.format(API_BASE_URL),
        include("osmchadjango.supervise.urls", namespace="supervise")
        ),
    path(
        '{}'.format(API_BASE_URL),
        include("osmchadjango.users.urls", namespace="users")
        ),
    ]

urlpatterns += [
    # Django Admin
    path('admin/', admin.site.urls),

    # api docs
    path(
        'api-docs/',
        SwaggerSchemaView.as_view(url_pattern=api_urls),
        name='api-docs'
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
