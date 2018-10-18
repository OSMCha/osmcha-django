# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.urls import re_path

from . import views


app_name = 'supervise'
urlpatterns = [
    re_path(
        r'^aoi/$',
        view=views.AOIListCreateAPIView.as_view(),
        name='aoi-list-create'
        ),
    re_path(
        r'^aoi/(?P<pk>[0-9a-f-]+)/$',
        view=views.AOIRetrieveUpdateDestroyAPIView.as_view(),
        name='aoi-detail'
        ),
    re_path(
        r'^aoi/(?P<pk>[0-9a-f-]+)/changesets/$',
        view=views.AOIListChangesetsAPIView.as_view(),
        name='aoi-list-changesets'
        ),
    re_path(
        r'^aoi/(?P<pk>[0-9a-f-]+)/changesets/feed/$',
        view=views.AOIListChangesetsFeedView(),
        name='aoi-changesets-feed'
        ),
    re_path(
        r'^aoi/(?P<pk>[0-9a-f-]+)/stats/$',
        view=views.AOIStatsAPIView.as_view(),
        name='aoi-stats'
        ),
    re_path(
        r'^blacklisted-users/$',
        view=views.BlacklistedUserListCreateAPIView.as_view(),
        name='blacklist-list-create'
        ),
    re_path(
        r'^blacklisted-users/(?P<uid>[0-9a-f-]+)/$',
        view=views.BlacklistedUserDetailAPIView.as_view(),
        name='blacklist-detail'
        ),
    ]
