# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.urls import re_path, path

from . import views

app_name = 'changeset'
urlpatterns = [
    re_path(
        r'^changesets/$',
        view=views.ChangesetListAPIView.as_view(),
        name='list'
    ),
    re_path(
        r'^changesets/suspect/$',
        view=views.SuspectChangesetListAPIView.as_view(),
        name='suspect-list'
    ),
    re_path(
        r'^changesets/no-suspect/$',
        view=views.NoSuspectChangesetListAPIView.as_view(),
        name='no-suspect-list'
    ),
    re_path(
        r'^changesets/harmful/$',
        view=views.HarmfulChangesetListAPIView.as_view(),
        name='harmful-list'
    ),
    re_path(
        r'^changesets/no-harmful/$',
        view=views.NoHarmfulChangesetListAPIView.as_view(),
        name='no-harmful-list'
    ),
    re_path(
        r'^changesets/checked/$',
        view=views.CheckedChangesetListAPIView.as_view(),
        name='checked-list'
    ),
    re_path(
        r'^changesets/unchecked/$',
        view=views.UncheckedChangesetListAPIView.as_view(),
        name='unchecked-list'
    ),
    re_path(
        r'^changesets/(?P<pk>\d+)/$',
        view=views.ChangesetDetailAPIView.as_view(),
        name='detail'
    ),
    re_path(
        r'^changesets/(?P<pk>\w+)/set-harmful/$',
        view=views.CheckChangeset.as_view({'put': 'set_harmful'}),
        name='set-harmful'
    ),
    re_path(
        r'^changesets/(?P<pk>\w+)/set-good/$',
        view=views.CheckChangeset.as_view({'put': 'set_good'}),
        name='set-good'
    ),
    re_path(
        r'^changesets/(?P<pk>\w+)/uncheck/$',
        view=views.uncheck_changeset,
        name='uncheck'
    ),
    re_path(
        r'^changesets/(?P<pk>\w+)/tags/(?P<tag_pk>\w+)/$',
        view=views.AddRemoveChangesetTagsAPIView.as_view(
            {'post': 'add_tag', 'delete': 'remove_tag'}
            ),
        name='tags'
    ),
    re_path(
        r'^changesets/(?P<pk>\w+)/comment/$',
        view=views.ChangesetCommentAPIView.as_view(
            {'post': 'post_comment', 'get': 'get_comments'}
            ),
        name='comment'
    ),
    re_path(
        r'^changesets/add-feature/$',
        view=views.add_feature,
        name='add-feature'
    ),
    re_path(
        r'^features/create/$',
        view=views.add_feature_v1,
        name='add-feature-v1'
    ),
    re_path(
        r'^whitelist-user/$',
        view=views.UserWhitelistListCreateAPIView.as_view(),
        name='whitelist-user'
    ),
    path(
        'whitelist-user/<str:whitelist_user>/',
        view=views.UserWhitelistDestroyAPIView.as_view(),
        name='delete-whitelist-user'
    ),
    re_path(
        r'^suspicion-reasons/$',
        view=views.SuspicionReasonsListAPIView.as_view(),
        name='suspicion-reasons-list'
    ),
    re_path(
        r'^suspicion-reasons/(?P<pk>\w+)/changesets/$',
        view=views.AddRemoveChangesetReasonsAPIView.as_view(
            {'post': 'add_reason_to_changesets', 'delete': 'remove_reason_from_changesets'}
            ),
        name='changeset-reasons'
    ),
    re_path(
        r'^tags/$',
        view=views.TagListAPIView.as_view(),
        name='tags-list'
    ),
    re_path(
        r'^stats/$',
        view=views.ChangesetStatsAPIView.as_view(),
        name='stats'
    ),
    re_path(
        r'^user-stats/(?P<uid>\w+)/$',
        view=views.UserStatsAPIView.as_view(),
        name='user-stats'
    ),
]
