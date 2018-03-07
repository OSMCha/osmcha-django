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
    re_path(r'^social-auth/$', views.SocialAuthAPIView.as_view(), name="social-auth"),
    ]
