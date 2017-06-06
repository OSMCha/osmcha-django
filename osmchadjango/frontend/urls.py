from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.filter_view 
    ),
    url(
        regex=r'^changesets/(?P<pk>\d+)/$',
        view=views.changeset_view
    ),

]
