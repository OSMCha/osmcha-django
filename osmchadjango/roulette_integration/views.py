from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import OrderingFilter

from .serializers import ChallengeIntegrationSerializer
from .models import ChallengeIntegration


class ChallengeIntegrationListCreateAPIView(ListCreateAPIView):
    """
    get:
    List all MapRoulette challenges.
    It can be ordered by 'created' or 'challenge_id'. The default ordering is by '-created'.

    post:
    Create a MapRoulette challenge.
    It requires a challenge_id and a list of SuspicionReasons. The challenge_id
    must be unique. This endpoint is restricted to staff users.
    """
    permission_classes = (IsAdminUser,)
    serializer_class = ChallengeIntegrationSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ('created', 'challenge_id')
    ordering = '-created'
    queryset = ChallengeIntegration.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChallengeIntegrationDetailAPIView(RetrieveUpdateDestroyAPIView):
    """
    get:
    Get details of a MapRoulette challenge.
    Only staff users can access it.

    put:
    Update an MapRoulette challenge.
    Only staff users can update it.

    patch:
    Update an MapRoulette challenge.
    Only staff users can update it.

    delete:
    Delete an MapRoulette challenge.
    Only staff users can delete it.
    """
    permission_classes = (IsAdminUser,)
    serializer_class = ChallengeIntegrationSerializer
    queryset = ChallengeIntegration.objects.all()
