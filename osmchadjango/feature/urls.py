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
        regex=r'^features/(?P<pk>\d+)$',
        view=views.FeatureDetailView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^features/api/suspicion$',
        view=views.suspicion_create,
        name='create_suspicion'
    ),
]