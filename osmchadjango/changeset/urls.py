# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth.decorators import login_required
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
    url(
        regex=r'^set-harmful/(?P<pk>\w+)/$',
        view=login_required(views.SetHarmfulChangeset.as_view()),
        name='set_harmful'
    ),
    url(
        regex=r'^set-good/(?P<pk>\w+)/$',
        view=login_required(views.SetGoodChangeset.as_view()),
        name='set_good'
    ),
    url(
        regex=r'^whitelist-user$',
        view='osmchadjango.changeset.views.whitelist_user',
        name='whitelist_user'
    ),
    url(
        regex=r'^remove-from-whitelist$',
        view='osmchadjango.changeset.views.remove_from_whitelist',
        name='remove_from_whitelist'
    )
]
