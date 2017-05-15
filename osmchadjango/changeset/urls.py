# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^changesets/$',
        view=views.ChangesetListAPIView.as_view(),
        name='list'
    ),
    url(
        regex=r'^changesets/suspect/$',
        view=views.SuspectChangesetListAPIView.as_view(),
        name='suspect-list'
    ),
    url(
        regex=r'^changesets/no-suspect/$',
        view=views.NoSuspectChangesetListAPIView.as_view(),
        name='no-suspect-list'
    ),
    url(
        regex=r'^changesets/harmful/$',
        view=views.HarmfulChangesetListAPIView.as_view(),
        name='harmful-list'
    ),
    url(
        regex=r'^changesets/no-harmful/$',
        view=views.NoHarmfulChangesetListAPIView.as_view(),
        name='no-harmful-list'
    ),
    url(
        regex=r'^changesets/checked/$',
        view=views.CheckedChangesetListAPIView.as_view(),
        name='checked-list'
    ),
    url(
        regex=r'^changesets/unchecked/$',
        view=views.UncheckedChangesetListAPIView.as_view(),
        name='unchecked-list'
    ),
    url(
        regex=r'^changesets/(?P<pk>\d+)/$',
        view=views.ChangesetDetailAPIView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^changesets/(?P<pk>\w+)/set-harmful/$',
        view=views.CheckChangeset.as_view({'put': 'set_harmful'}),
        name='set_harmful'
    ),
    url(
        regex=r'^changesets/(?P<pk>\w+)/set-good/$',
        view=views.CheckChangeset.as_view({'put': 'set_good'}),
        name='set_good'
    ),
    url(
        regex=r'^changesets/(?P<pk>\w+)/uncheck/$',
        view=views.uncheck_changeset,
        name='uncheck'
    ),
    url(
        regex=r'^changesets/(?P<pk>\w+)/add-tag/(?P<tag_pk>\w+)/$',
        view=views.AddRemoveChangesetTagsAPIView.as_view({'put': 'add_tag'}),
        name='add-tag'
    ),
    url(
        regex=r'^changesets/(?P<pk>\w+)/remove-tag/(?P<tag_pk>\w+)/$',
        view=views.AddRemoveChangesetTagsAPIView.as_view({'put': 'remove_tag'}),
        name='remove-tag'
    ),
    url(
        regex=r'^whitelist-user/$',
        view=views.UserWhitelistListCreateAPIView.as_view(),
        name='whitelist-user'
    ),
    url(
        regex=r'^whitelist-user/(?P<whitelist_user>\w+)/$',
        view=views.UserWhitelistDestroyAPIView.as_view(),
        name='delete-whitelist-user'
    ),
    url(
        regex=r'^suspicion-reasons/$',
        view=views.SuspicionReasonsListAPIView.as_view(),
        name='suspicion-reasons-list'
    ),
    url(
        regex=r'^tags/$',
        view=views.TagListAPIView.as_view(),
        name='tags-list'
    ),
    url(
        regex=r'^stats/$',
        view=views.ChangesetStatsAPIView.as_view(),
        name='stats'
    ),
    url(
        regex=r'^user-stats/(?P<uid>\w+)/$',
        view=views.UserStatsAPIView.as_view(),
        name='user-stats'
    ),
]
