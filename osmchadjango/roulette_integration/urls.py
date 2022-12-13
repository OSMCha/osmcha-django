from django.urls import path

from . import views

app_name = "roulette_integration"
urlpatterns = [
    path(
        "challenges/",
        view=views.ChallengeIntegrationListCreateAPIView.as_view(),
        name="list-create",
    ),
    path(
        "challenges/<int:pk>/",
        view=views.ChallengeIntegrationDetailAPIView.as_view(),
        name="detail",
    ),
]
