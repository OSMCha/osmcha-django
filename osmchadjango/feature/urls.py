# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^features$',
        view=views.FeatureListView.as_view(),
        name='features'
    ),
    url(
        regex=r'^(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.FeatureDetailView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^features/api/suspicion/$',
        view=views.suspicion_create,
        name='create_suspicion_without_trailing_slash'
    ),
    url(
        regex=r'^features/api/suspicion$',
        view=views.suspicion_create,
        name='create_suspicion'
    ),
    url(
        regex=r'^(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/geojson$',
        view=views.get_geojson,
        name='get_geojson'
    ),
    url(
        regex=r'^set-harmful/(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=login_required(views.SetHarmfulFeature.as_view()),
        name='set_harmful'
    ),
    url(
        regex=r'^set-good/(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=login_required(views.SetGoodFeature.as_view()),
        name='set_good'
    ),
    url(
        regex=r'^features/whitelist-user$',
        view=views.whitelist_user,
        name='whitelist_user'
    ),
]
