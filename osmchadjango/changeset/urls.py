# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth.decorators import login_required
from django.conf.urls import url

from . import views

urlpatterns = [
    # URL pattern for the UserListView
    url(
        regex=r'^$',
        view=views.ChangesetListAPIView.as_view(),
        name='list'
    ),
    url(
        regex=r'^suspect$',
        view=views.SuspectChangesetListAPIView.as_view(),
        name='suspect-list'
    ),
    url(
        regex=r'^no-suspect$',
        view=views.NoSuspectChangesetListAPIView.as_view(),
        name='no-suspect-list'
    ),
    url(
        regex=r'^harmful$',
        view=views.HarmfulChangesetListAPIView.as_view(),
        name='harmful-list'
    ),
    url(
        regex=r'^no-harmful$',
        view=views.NoHarmfulChangesetListAPIView.as_view(),
        name='no-harmful-list'
    ),
    url(
        regex=r'^checked$',
        view=views.CheckedChangesetListAPIView.as_view(),
        name='checked-list'
    ),
    url(
        regex=r'^unchecked$',
        view=views.UncheckedChangesetListAPIView.as_view(),
        name='unchecked-list'
    ),
    url(
        regex=r'^(?P<pk>\d+)/$',
        view=views.ChangesetDetailAPIView.as_view(),
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
        view=views.whitelist_user,
        name='whitelist_user'
    ),
    url(
        regex=r'^remove-from-whitelist$',
        view=views.remove_from_whitelist,
        name='remove_from_whitelist'
    ),
    url(
        regex=r'^stats$',
        view=views.stats,
        name='stats'
    ),
    url(
        regex=r'^all-whitelist-users$',
        view=views.all_whitelist_users,
        name='all_whitelist_users'
    ),
    url(
        regex=r'^all-blacklist-users$',
        view=views.all_blacklist_users,
        name='all_blacklist_users'
    ),
    url(
        regex=r'^checked-changesets$',
        view=views.CheckedChangesetsView.as_view(),
        name='checked_changesets'
    ),
    url(
        regex=r'^harmful-changesets$',
        view=views.HarmfulChangesetsView.as_view(),
        name='harmful_changesets'
    ),
    url(
        regex=r'^undo-changeset-marking/(?P<pk>\w+)/$',
        view=views.undo_changeset_marking,
        name='undo_changeset_marking'
    )
]
