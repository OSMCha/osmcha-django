# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import re_path

from . import views


app_name = 'feature'
urlpatterns = [
    re_path(
        r'^features/$',
        view=views.FeatureListAPIView.as_view(),
        name='list'
    ),
    re_path(
        r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.FeatureDetailAPIView.as_view(),
        name='detail'
    ),
    # re_path(
    #     r'^features/create/$',
    #     view=views.create_feature,
    #     name='create'
    # ),
    re_path(
        r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/set-harmful/$',
        view=views.CheckFeature.as_view({'put': 'set_harmful'}),
        name='set-harmful'
    ),
    re_path(
        r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/set-good/$',
        view=views.CheckFeature.as_view({'put': 'set_good'}),
        name='set-good'
    ),
    re_path(
        r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/uncheck/$',
        view=views.uncheck_feature,
        name='uncheck'
    ),
    re_path(
        r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/tags/(?P<tag_pk>\w+)/$',
        view=views.AddRemoveFeatureTagsAPIView.as_view(
            {'post': 'add_tag', 'delete': 'remove_tag'}
            ),
        name='tags'
    ),
]
