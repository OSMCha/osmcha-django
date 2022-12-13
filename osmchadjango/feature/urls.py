from django.urls import path

from . import views


app_name = "feature"
urlpatterns = [
    path("features/", view=views.FeatureListAPIView.as_view(), name="list"),
    path(
        "features/<int:changeset>-<str:slug>/",
        view=views.FeatureDetailAPIView.as_view(),
        name="detail",
    ),
    # path(
    #     'features/create/',
    #     view=views.create_feature,
    #     name='create'
    # ),
    path(
        "features/<int:changeset>-<str:slug>/set-harmful/",
        view=views.CheckFeature.as_view({"put": "set_harmful"}),
        name="set-harmful",
    ),
    path(
        "features/<int:changeset>-<str:slug>/set-good/",
        view=views.CheckFeature.as_view({"put": "set_good"}),
        name="set-good",
    ),
    path(
        "features/<int:changeset>-<str:slug>/uncheck/",
        view=views.uncheck_feature,
        name="uncheck",
    ),
    path(
        "features/<int:changeset>-<str:slug>/tags/<int:tag_pk>/",
        view=views.AddRemoveFeatureTagsAPIView.as_view(
            {"post": "add_tag", "delete": "remove_tag"}
        ),
        name="tags",
    ),
]
