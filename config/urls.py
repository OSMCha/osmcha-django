# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.views import defaults
from django.views import static as static_views
from osmchadjango.frontend import urls as frontend_urls

from .docs import SwaggerSchemaView

API_BASE_URL = 'api/v1/'

urlpatterns = []

# If static files are not intercepted by the web-server, serve them with the dev-server:
if settings.DEBUG is False:   # if DEBUG is True it will be served automatically
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', static_views.serve, {'document_root': settings.STATIC_ROOT}),
        ]

api_urls = [
    url(
        r'^{}'.format(API_BASE_URL),
        include("osmchadjango.changeset.urls", namespace="changeset")
        ),
    url(
        r'^{}'.format(API_BASE_URL),
        include("osmchadjango.feature.urls", namespace="feature")
        ),
    url(
        r'^{}'.format(API_BASE_URL),
        include("osmchadjango.supervise.urls", namespace="supervise")
        ),
    url(
        r'^{}'.format(API_BASE_URL),
        include("osmchadjango.users.urls", namespace="users")
        ),
    url(
        r'^{}'.format(API_BASE_URL),
        include("osmchadjango.priority.urls", namespace="priority")
        ),
    ]

urlpatterns += [
    # Django Admin
    url(r'^admin/', include(admin.site.urls)),

    # api docs
    url(r'^api-docs/$', SwaggerSchemaView.as_view(url_pattern=api_urls), name='api-docs'),

    # include api_urls
    url(
        r'^',
        include(api_urls)
        ),

    # frontend urls
    url(r'^', include(frontend_urls, namespace="frontend")),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    import debug_toolbar
    urlpatterns += [
        url(r'^400/$', defaults.bad_request),
        url(r'^403/$', defaults.permission_denied),
        url(r'^404/$', defaults.page_not_found),
        url(r'^500/$', defaults.server_error),
        url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
