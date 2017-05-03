# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.AOIListCreateAPIView.as_view(),
        name='aoi-list-create'
        ),
    url(
        regex=r'^(?P<pk>[0-9a-f-]+)/$',
        view=views.AOIRetrieveUpdateDestroyAPIView.as_view(),
        name='aoi-detail'
        ),
    url(
        regex=r'^(?P<pk>[0-9a-f-]+)/changesets/$',
        view=views.AOIListChangesetsAPIView.as_view(),
        name='aoi-list-changesets'
        ),
    url(
        regex=r'^(?P<pk>[0-9a-f-]+)/features/$',
        view=views.AOIListFeaturesAPIView.as_view(),
        name='aoi-list-features'
        ),
    url(
        regex=r'^(?P<pk>[0-9a-f-]+)/stats/$',
        view=views.AOIStatsAPIView.as_view(),
        name='aoi-stats'
        ),
    ]
