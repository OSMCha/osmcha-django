# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^areas-of-interest/$',
        view=views.AOIListCreateAPIView.as_view(),
        name='list-create'
        ),
    ]
