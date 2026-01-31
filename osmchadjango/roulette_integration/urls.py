# -*- coding: utf-8 -*-

from django.urls import re_path

from . import views


app_name = 'roulette_integration'
urlpatterns = [
    re_path(
        r'^challenges/$',
        view=views.ChallengeIntegrationListCreateAPIView.as_view(),
        name='list-create'
        ),
    re_path(
        r'^challenges/(?P<pk>\d+)/$',
        view=views.ChallengeIntegrationDetailAPIView.as_view(),
        name='detail'
        ),
    ]
