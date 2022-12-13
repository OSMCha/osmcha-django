from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import views


app_name = "frontend"
urlpatterns = [
    path(
        "", view=TemplateView.as_view(template_name="frontend/index.html"), name="index"
    ),
    path(
        "index.html",
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name="index.html",
    ),
    path(
        "oauth-landing.html",
        view=TemplateView.as_view(template_name="frontend/oauth-landing.html"),
        name="oauth-landing",
    ),
    path(
        "local-landing.html",
        view=TemplateView.as_view(template_name="frontend/local-landing.html"),
        name="local-landing",
    ),
    path("service-worker.js", view=views.service_worker_view, name="service-worker"),
    path("favicon.ico", view=views.favicon_view, name="favicon"),
    path(
        "changesets/<int:pk>/",
        view=TemplateView.as_view(template_name="frontend/index.html"),
        name="changeset-detail",
    ),
    path(
        "<int:pk>/",
        view=RedirectView.as_view(pattern_name="frontend:changeset-detail"),
        name="changeset-detail-redirect",
    ),
]
