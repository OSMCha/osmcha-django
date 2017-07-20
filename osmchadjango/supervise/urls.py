# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^aoi/$',
        view=views.AOIListCreateAPIView.as_view(),
        name='aoi-list-create'
        ),
    url(
        regex=r'^aoi/(?P<pk>[0-9a-f-]+)/$',
        view=views.AOIRetrieveUpdateDestroyAPIView.as_view(),
        name='aoi-detail'
        ),
    url(
        regex=r'^aoi/(?P<pk>[0-9a-f-]+)/changesets/$',
        view=views.AOIListChangesetsAPIView.as_view(),
        name='aoi-list-changesets'
        ),
    url(
        regex=r'^aoi/(?P<pk>[0-9a-f-]+)/features/$',
        view=views.AOIListFeaturesAPIView.as_view(),
        name='aoi-list-features'
        ),
    url(
        regex=r'^aoi/(?P<pk>[0-9a-f-]+)/stats/$',
        view=views.AOIStatsAPIView.as_view(),
        name='aoi-stats'
        ),
    url(
        regex=r'^blacklisted-users/$',
        view=views.BlacklistedUserListCreateAPIView.as_view(),
        name='blacklist-list-create'
        ),
    url(
        regex=r'^blacklisted-users/(?P<uid>[0-9a-f-]+)/$',
        view=views.BlacklistedUserDetailAPIView.as_view(),
        name='blacklist-detail'
        ),
    ]
