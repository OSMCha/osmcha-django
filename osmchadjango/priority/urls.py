from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^priorities/$',
        view=views.PriorityCreateAPIView.as_view(),
        name='create'
    ),
    url(
        regex=r'^priorities/(?P<changeset>[0-9a-f-]+)/$',
        view=views.PriorityDestroyAPIView.as_view(),
        name='delete'
    ),
    url(
        regex=r'^priority-changesets/$',
        view=views.PriorityChangesetsListAPIView.as_view(),
        name='list-changesets'
    ),
]
