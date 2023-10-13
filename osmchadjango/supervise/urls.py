from django.urls import path

from . import views

app_name = 'supervise'
urlpatterns = [
    path(
        'aoi/',
        view=views.AOIListCreateAPIView.as_view(),
        name='aoi-list-create'
    ),
    path(
        'aoi/<str:pk>/',
        view=views.AOIRetrieveUpdateDestroyAPIView.as_view(),
        name='aoi-detail'
    ),
    path(
        'aoi/<str:pk>/changesets/',
        view=views.AOIListChangesetsAPIView.as_view(),
        name='aoi-list-changesets'
    ),
    path(
        'aoi/<str:pk>/changesets/feed/',
        view=views.AOIListChangesetsFeedView(),
        name='aoi-changesets-feed'
    ),
    path(
        'aoi/<str:pk>/stats/',
        view=views.AOIStatsAPIView.as_view(),
        name='aoi-stats'
    ),
    path(
        'blacklisted-users/',
        view=views.BlacklistedUserListCreateAPIView.as_view(),
        name='blacklist-list-create'
    ),
    path(
        'blacklisted-users/<str:pk>/',
        view=views.BlacklistedUserDetailAPIView.as_view(),
        name='blacklist-detail'
    ),
]
