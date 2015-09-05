# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    # URL pattern for the UserListView
    url(
        regex=r'^$',
        view=views.ChangesetListView.as_view(),
        name='home'
    ),
    url(
        regex=r'^(?P<pk>\w+)/$',
        view=views.ChangesetDetailView.as_view(),
        name='detail'
    ),
]
