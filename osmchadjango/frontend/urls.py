from __future__ import absolute_import, unicode_literals

from django.urls import re_path
from django.views.generic.base import TemplateView, RedirectView

from . import views


app_name = 'frontend'
urlpatterns = [
    re_path(
        r'^$',
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name='index'
    ),
    re_path(
        r'^index.html',
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name='index.html'
    ),
    re_path(
        r'^oauth-landing.html',
        view=TemplateView.as_view(template_name="frontend/oauth-landing.html"),
        name='oauth-landing'
    ),
    re_path(
        r'^local-landing.html',
        view=TemplateView.as_view(template_name="frontend/local-landing.html"),
        name='local-landing'
    ),
    re_path(
        r'^service-worker.js',
        view=views.service_worker_view,
        name='service-worker'
    ),
    re_path(
        r'^favicon.ico',
        view=views.favicon_view,
        name='favicon'
    ),
    re_path(
        r'^changesets/(?P<pk>\d+)/$',
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name='changeset-detail'
    ),
    re_path(
        r'^(?P<pk>\d+)/$',
        view=RedirectView.as_view(pattern_name='frontend:changeset-detail'),
        name='changeset-detail-redirect'
    )
]
