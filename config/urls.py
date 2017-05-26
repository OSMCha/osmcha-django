# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views import defaults
from django.views import static as static_views

from .docs import SwaggerSchemaView

API_BASE_URL = 'api/v1/'

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
    ]

urlpatterns = [
    url(r'^about/$', TemplateView.as_view(template_name='pages/about.html'), name="about"),
    # Django Admin
    url(r'^admin/', include(admin.site.urls)),
    # redirect user to frontend url after OSM authentication
    url(r'^frontend/$',
        RedirectView.as_view(
            url=settings.EXTERNAL_FRONTEND_URL,
            query_string=True
            )
        ),
    # api docs
    url(r'^api-docs/$', SwaggerSchemaView.as_view(url_pattern=api_urls), name='api-docs'),
    url(r'^$', SwaggerSchemaView.as_view(url_pattern=api_urls), name='api-docs'),
    # include api_urls
    url(
        r'^',
        include(api_urls)
        ),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', defaults.bad_request),
        url(r'^403/$', defaults.permission_denied),
        url(r'^404/$', defaults.page_not_found),
        url(r'^500/$', defaults.server_error),
        ]


# If static files are not intercepted by the web-server, serve them with the dev-server:
if settings.DEBUG is False:   # if DEBUG is True it will be served automatically
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', static_views.serve, {'document_root': settings.STATIC_ROOT}),
        ]
