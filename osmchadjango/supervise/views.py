from rest_framework.generics import (
    ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
    )
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS

from ..changeset.serializers import ChangesetSerializer, ChangesetSerializerToStaff
from ..changeset.views import StandardResultsSetPagination
from .models import AreaOfInterest
from .serializers import AreaOfInterestSerializer


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            return obj.user == request.user


class AOIListCreateAPIView(ListCreateAPIView):
    """
    get:
    List the Areas of Interest of the current logged user.

    post:
    Create an Area of Interest. It requires authentication.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = AreaOfInterestSerializer

    def get_queryset(self):
        return AreaOfInterest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AOIRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = AreaOfInterest.objects.all()
    serializer_class = AreaOfInterestSerializer
    permission_classes = (IsOwnerOrReadOnly,)


class AOIListChangesetsAPIView(ListAPIView):
    """List the changesets that matches the filters and intersects with the
    geometry of an Area Of Interest. It supports pagination and return the data
    in the same way as the changeset list endpoint.
    """
    queryset = AreaOfInterest.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ChangesetSerializerToStaff
        else:
            return ChangesetSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_object().changesets()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
