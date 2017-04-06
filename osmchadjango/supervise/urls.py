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
        view=views.AOIRetrieveAPIView.as_view(),
        name='aoi-detail'
        ),
    url(
        regex=r'^aoi/(?P<pk>[0-9a-f-]+)/changesets/$',
        view=views.AOIListChangesetsAPIView.as_view(),
        name='aoi-list-changesets'
        ),
    ]
