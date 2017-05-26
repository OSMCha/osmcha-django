# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^users/$',
        view=views.CurrentUserDetailAPIView.as_view(),
        name='detail'
        ),
    url(r'^social-auth/$', views.SocialAuthView.as_view(), name="social-auth"),
    ]
