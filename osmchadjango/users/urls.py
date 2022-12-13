from django.urls import path

from . import views


app_name = "users"
urlpatterns = [
    path("users/", view=views.CurrentUserDetailAPIView.as_view(), name="detail"),
    path("social-auth/", view=views.SocialAuthAPIView.as_view(), name="social-auth"),
    path(
        "update-deleted-users/",
        view=views.update_deleted_users,
        name="update-deleted-users",
    ),
    path(
        "mapping-team/",
        views.MappingTeamListCreateAPIView.as_view(),
        name="mapping-team",
    ),
    path(
        "mapping-team/<int:pk>/",
        views.MappingTeamDetailAPIView.as_view(),
        name="mapping-team-detail",
    ),
    path(
        "mapping-team/<int:pk>/trust/",
        view=views.MappingTeamTrustingAPIView.as_view({"put": "set_trusted"}),
        name="trust-mapping-team",
    ),
    path(
        "mapping-team/<int:pk>/untrust/",
        view=views.MappingTeamTrustingAPIView.as_view({"put": "set_untrusted"}),
        name="untrust-mapping-team",
    ),
]
