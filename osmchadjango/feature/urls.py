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
        regex=r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/$',
        view=views.FeatureDetailAPIView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^features/create/$',
        view=views.create_feature,
        name='create'
    ),
    url(
        regex=r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/set-harmful/$',
        view=views.CheckFeature.as_view({'put': 'set_harmful'}),
        name='set-harmful'
    ),
    url(
        regex=r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/set-good/$',
        view=views.CheckFeature.as_view({'put': 'set_good'}),
        name='set-good'
    ),
    url(
        regex=r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/add-tag/(?P<tag_pk>\w+)/$',
        view=views.AddRemoveFeatureTagsAPIView.as_view({'put': 'add_tag'}),
        name='add-tag'
    ),
    url(
        regex=r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/remove-tag/(?P<tag_pk>\w+)/$',
        view=views.AddRemoveFeatureTagsAPIView.as_view({'put': 'remove_tag'}),
        name='remove-tag'
    ),
    url(
        regex=r'^features/(?P<changeset>\d+)-(?P<slug>[a-zA-Z0-9-]+)/uncheck/$',
        view=views.uncheck_feature,
        name='uncheck'
    ),
]
