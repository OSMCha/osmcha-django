from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser

from ..changeset.views import ChangesetListAPIView
from .models import Priority
from .serializers import PriorityCreationSerializer


class PriorityCreateAPIView(CreateAPIView):
    """Add a Changeset to the Priority list.
    Only staff users have permission to use this endpoint.
    """
    queryset = Priority.objects.all()
    serializer_class = PriorityCreationSerializer
    permission_classes = (IsAdminUser,)


class PriorityDestroyAPIView(DestroyAPIView):
    """Remove a Changeset from the Priority list.
    Only staff users have permission to use this endpoint.
    """
    queryset = Priority.objects.all()
    serializer_class = PriorityCreationSerializer
    lookup_field = 'changeset'
    permission_classes = (IsAdminUser,)


class PriorityChangesetsListAPIView(ChangesetListAPIView):
    """List priority Changesets to be reviewed by the data team.
    Only staff users can access this endpoint.
    """
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        return self.queryset.filter(
            id__in=Priority.objects.values_list('changeset', flat=True)
            )
