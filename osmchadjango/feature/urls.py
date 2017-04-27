# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^features/$',
        view=views.FeatureListAPIView.as_view(),
        name='list'
    ),
    url(
        regex=r'^(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.FeatureDetailAPIView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^features/create/$',
        view=views.create_feature,
        name='create'
    ),
    url(
        regex=r'^set-harmful/(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.set_harmful_feature,
        name='set-harmful'
    ),
    url(
        regex=r'^set-good/(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.set_good_feature,
        name='set-good'
    ),
    url(
        regex=r'^uncheck/(?P<changeset>\d+)/features/(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.uncheck_feature,
        name='uncheck'
    ),
]
