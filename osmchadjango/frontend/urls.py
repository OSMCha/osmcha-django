from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.views.generic.base import TemplateView, RedirectView

from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name='index'
    ),
    url(
        regex=r'^index.html',
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name='index.html'
    ),
    url(
        regex=r'^oauth-landing.html',
        view=TemplateView.as_view(template_name="frontend/oauth-landing.html"),
        name='oauth-landing'
    ),
    url(
        regex=r'^local-landing.html',
        view=TemplateView.as_view(template_name="frontend/local-landing.html"),
        name='local-landing'
    ),
    url(
        regex=r'^favicon.ico',
        view=views.favicon_view,
        name='favicon'
    ),
    url(
        regex=r'^changesets/(?P<pk>\d+)/$',
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name='changeset-detail'
    ),
    url(
        regex=r'^(?P<pk>\d+)/$',
        view=RedirectView.as_view(pattern_name='frontend:changeset-detail'),
        name='changeset-detail-redirect'
    ),
    url(
        regex=r'^(?P<filename>[a-zA-Z0-9-]+).json',
        view=views.json_static_view
    ),
    url(
        regex=r'^(?P<filename>[a-zA-Z0-9-]+).js',
        view=views.js_static_view
    ),
]
