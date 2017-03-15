# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults
from django.views import static as static_views

from rest_framework.documentation import include_docs_urls

urlpatterns = [
    url(r'^about/$', TemplateView.as_view(template_name='pages/about.html'), name="about"),

    # Django Admin
    url(r'^admin/', include(admin.site.urls)),

    # django-rest-social-auth token urls
    url(r'^login/', include('rest_social_auth.urls_token')),
    # User management
    url(r'^users/', include("osmchadjango.users.urls", namespace="users")),

    # Your stuff: custom urls includes go here
    url(r'^', include("osmchadjango.changeset.urls", namespace="changeset")),
    url(r'^', include("osmchadjango.feature.urls", namespace="feature")),
    url(r'^api-docs/', include_docs_urls(title='OSMCHA API'))



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
if settings.DEBUG is False:   #if DEBUG is True it will be served automatically
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', static_views.serve, {'document_root': settings.STATIC_ROOT}),
    ]
