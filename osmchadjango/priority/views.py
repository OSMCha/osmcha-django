from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser

from ..changeset.views import ChangesetListAPIView, ChangesetStatsAPIView
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
    It's possible to apply the same filter parameters that are available in the
    changeset list endpoint. Access restricted to staff users.
    """
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        return self.queryset.filter(
            id__in=Priority.objects.values_list('changeset', flat=True)
            )


class PriorityChangesetsStatsAPIView(ChangesetStatsAPIView):
    """Get stats about Priority Changesets.
    It will return the total number of checked and harmful changesets, the
    number of users with harmful changesets and the number of checked and
    harmful changesets by Suspicion Reason and by Tag. It's possible to filter
    the changesets using the same filter parameters of the changeset list
    endpoint. Access restricted to staff users.
    """
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        return self.queryset.filter(
            id__in=Priority.objects.values_list('changeset', flat=True)
            )
