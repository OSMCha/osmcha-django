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
        regex=r'^(?P<changeset_id>\w+)/suspicious_feature/(?P<osm_id>\w+)/geojson$',
        view='osmchadjango.changeset.views.suspicious_feature_geojson',
        name='suspicious_feature_geojson'
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
        regex=r'^api/suspicion$',
        view='osmchadjango.changeset.views.suspicion_create',
        name='create_suspicion'
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
    ),
    url(
        regex=r'^stats$',
        view='osmchadjango.changeset.views.stats',
        name='stats'
    ),
    url(
        regex=r'^all-whitelist-users$',
        view='osmchadjango.changeset.views.all_whitelist_users',
        name='all_whitelist_users'
    ),
    url(
        regex=r'^all-blacklist-users$',
        view='osmchadjango.changeset.views.all_blacklist_users',
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
    )
]
