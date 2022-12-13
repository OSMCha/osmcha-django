from django.urls import path

from . import views

app_name = "changeset"
urlpatterns = [
    path("changesets/", view=views.ChangesetListAPIView.as_view(), name="list"),
    path(
        "changesets/suspect/",
        view=views.SuspectChangesetListAPIView.as_view(),
        name="suspect-list",
    ),
    path(
        "changesets/no-suspect/",
        view=views.NoSuspectChangesetListAPIView.as_view(),
        name="no-suspect-list",
    ),
    path(
        "changesets/harmful/",
        view=views.HarmfulChangesetListAPIView.as_view(),
        name="harmful-list",
    ),
    path(
        "changesets/no-harmful/",
        view=views.NoHarmfulChangesetListAPIView.as_view(),
        name="no-harmful-list",
    ),
    path(
        "changesets/checked/",
        view=views.CheckedChangesetListAPIView.as_view(),
        name="checked-list",
    ),
    path(
        "changesets/unchecked/",
        view=views.UncheckedChangesetListAPIView.as_view(),
        name="unchecked-list",
    ),
    path(
        "changesets/<int:pk>/",
        view=views.ChangesetDetailAPIView.as_view(),
        name="detail",
    ),
    path(
        "changesets/<int:pk>/tag-changes/",
        view=views.SetChangesetTagChangesAPIView.as_view({"post": "set_tag_changes"}),
        name="set-tag-changes",
    ),
    path(
        "changesets/<int:pk>/set-harmful/",
        view=views.CheckChangeset.as_view({"put": "set_harmful"}),
        name="set-harmful",
    ),
    path(
        "changesets/<int:pk>/set-good/",
        view=views.CheckChangeset.as_view({"put": "set_good"}),
        name="set-good",
    ),
    path("changesets/<int:pk>/uncheck/", view=views.uncheck_changeset, name="uncheck"),
    path(
        "changesets/<int:pk>/review-feature/<str:type>-<int:id>/",
        view=views.ReviewFeature.as_view(
            {"put": "set_harmful_feature", "delete": "remove_harmful_feature"}
        ),
        name="review-harmful-feature",
    ),
    path(
        "changesets/<int:pk>/tags/<int:tag_pk>/",
        view=views.AddRemoveChangesetTagsAPIView.as_view(
            {"post": "add_tag", "delete": "remove_tag"}
        ),
        name="tags",
    ),
    path(
        "changesets/<int:pk>/comment/",
        view=views.ChangesetCommentAPIView.as_view({"post": "post_comment"}),
        name="comment",
    ),
    path("changesets/add-feature/", view=views.add_feature, name="add-feature"),
    path("features/create/", view=views.add_feature_v1, name="add-feature-v1"),
    path(
        "whitelist-user/",
        view=views.UserWhitelistListCreateAPIView.as_view(),
        name="whitelist-user",
    ),
    path(
        "whitelist-user/<str:whitelist_user>/",
        view=views.UserWhitelistDestroyAPIView.as_view(),
        name="delete-whitelist-user",
    ),
    path(
        "suspicion-reasons/",
        view=views.SuspicionReasonsListAPIView.as_view(),
        name="suspicion-reasons-list",
    ),
    path(
        "suspicion-reasons/<int:pk>/changesets/",
        view=views.AddRemoveChangesetReasonsAPIView.as_view(
            {
                "post": "add_reason_to_changesets",
                "delete": "remove_reason_from_changesets",
            }
        ),
        name="changeset-reasons",
    ),
    path("tags/", view=views.TagListAPIView.as_view(), name="tags-list"),
    path("stats/", view=views.ChangesetStatsAPIView.as_view(), name="stats"),
    path("user-stats/<int:uid>/", view=views.user_stats, name="user-stats"),
]
