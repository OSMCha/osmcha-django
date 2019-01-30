# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.urls import re_path

from . import views


app_name = 'users'
urlpatterns = [
    re_path(
        r'^users/$',
        view=views.CurrentUserDetailAPIView.as_view(),
        name='detail'
        ),
    re_path(
        r'^social-auth/$',
        views.SocialAuthAPIView.as_view(),
        name="social-auth"
        ),
    re_path(
        r'^mapping-team/$',
        views.MappingTeamListCreateAPIView.as_view(),
        name="mapping-team"
        ),
    re_path(
        r'^mapping-team/(?P<pk>\d+)/$',
        views.MappingTeamDetailAPIView.as_view(),
        name="mapping-team-detail"
        ),
    re_path(
        r'^mapping-team/(?P<pk>\d+)/trust/$',
        view=views.MappingTeamTrustingAPIView.as_view({'put': 'set_trusted'}),
        name='trust-mapping-team'
    ),
    re_path(
        r'^mapping-team/(?P<pk>\d+)/untrust/$',
        view=views.MappingTeamTrustingAPIView.as_view({'put': 'set_untrusted'}),
        name='untrust-mapping-team'
    ),
    ]
