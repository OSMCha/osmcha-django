from __future__ import unicode_literals

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.feeds import Feed
from django.urls import reverse

from rest_framework.generics import (
    ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView,
    get_object_or_404
    )
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    IsAuthenticated, BasePermission, SAFE_METHODS
    )

from ..changeset.serializers import (
    ChangesetSerializer, ChangesetSerializerToStaff, ChangesetStatsSerializer
    )
from ..changeset.views import StandardResultsSetPagination
from .models import AreaOfInterest, BlacklistedUser
from .serializers import (
    AreaOfInterestSerializer, BlacklistSerializer,
    AreaOfInterestAnonymousSerializer
    )


def get_geometry_from_filters(data):
    if 'filters' in data.keys():
        if 'geometry' in data['filters'].keys():
            geometry = data['filters'].get('geometry')
            return GEOSGeometry('{}'.format(geometry))
        elif 'in_bbox' in data['filters'].keys():
            geometry = data['filters'].get('in_bbox').split(',')
            return Polygon.from_bbox(geometry)
        else:
            return None
    else:
        return None


class IsOwnerOrReadOnly(BasePermission):
    """Object-level permission to only allow owners of an object to edit it."""

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
    List the Areas of Interest of the request user.
    It can be ordered by 'name' or 'date'. The default ordering is by '-date'.

    post:
    Create an Area of Interest.
    It needs to receive the filter parameters and a name. The AoI name must be
    unique to a user. This endpoint requires authentication.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = AreaOfInterestSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ('date', 'name')
    ordering = '-date'

    def get_queryset(self):
        if self.request:
            return AreaOfInterest.objects.filter(user=self.request.user)
        else:
            AreaOfInterest.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            geometry=get_geometry_from_filters(self.request.data)
            )


class AOIRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    get:
    Get details about an Area of Interest.

    put:
    Update an Area of Interest.
    Only the user that created an Area of Interest has permissions to update it.

    patch:
    Update an Area of Interest.
    Only the user that created an Area of Interest has permissions to update it.

    delete:
    Delete an Area of Interest.
    Only the user that created an Area of Interest has permissions to delete it.
    """
    queryset = AreaOfInterest.objects.all()
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def perform_update(self, serializer):
        serializer.save(
            geometry=get_geometry_from_filters(self.request.data)
            )

    def get_serializer_class(self):
        if self.request and self.request.user.is_authenticated:
            return AreaOfInterestSerializer
        else:
            return AreaOfInterestAnonymousSerializer


class AOIListChangesetsFeedView(Feed):
    """Feed view with the last 50 changesets that matches an Area of Interest.
    """

    def get_object(self, request, pk):
        self.feed_id = pk
        return AreaOfInterest.objects.get(pk=pk)

    def title(self, obj):
        return 'Changesets of Area of Interest {} by {}'.format(
            obj.name if obj.name else 'Unnamed', obj.user
        )

    def link(self, obj):
        return reverse('supervise:aoi-detail', args=[obj.id])

    def items(self, obj):
        return obj.changesets()[:50]

    def item_title(self, item):
        return 'Changeset {} by {}'.format(item.id, item.user)

    def item_geometry(self, item):
        return item.bbox

    def item_link(self, item):
        return '{}{}'.format(reverse(
            'frontend:changeset-detail',
            args=[item.id]
            ), '?aoi={}'.format(self.feed_id))

    def item_pubdate(self, item):
        return item.date

    def item_description(self, item):
        description_items = []
        if item.comment:
            description_items.append(item.comment)
        description_items.append('Create: {}, Modify: {}, Delete: {}'.format(
            item.create, item.modify, item.delete
            ))
        if item.is_suspect:
            suspect = 'Changeset flagged for: '
            suspect += ', '.join([reason.name for reason in item.reasons.all()])
            description_items.append(suspect)
        if item.checked:
            if item.harmful:
                description_items.append(
                    'Marked as harmful by {}'.format(item.check_user.username)
                    )
            elif item.harmful is False:
                description_items.append(
                    'Marked as good by {}'.format(item.check_user.username)
                    )

        return '<br>'.join(description_items)


class AOIListChangesetsAPIView(ListAPIView):
    """List the changesets that matches the filters and intersects with the
    geometry of an Area Of Interest. It supports pagination and return the data
    in the same way as the changeset list endpoint.
    """
    queryset = AreaOfInterest.objects.all()
    pagination_class = StandardResultsSetPagination
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ChangesetSerializerToStaff
        else:
            return ChangesetSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_object().changesets().select_related(
            'check_user'
            ).prefetch_related('tags', 'reasons')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AOIStatsAPIView(ListAPIView):
    """Return the statistics of the changesets that matches an Area of Interest.
    The data will be in the same format as the Changeset Stats view.
    """
    queryset = AreaOfInterest.objects.all()
    serializer_class = ChangesetStatsSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_object().changesets().select_related(
            'check_user'
            ).prefetch_related('tags', 'reasons')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BlacklistedUserListCreateAPIView(ListCreateAPIView):
    """
    get:
    List BlacklistedUsers.
    Access restricted to staff users.
    post:
    Add a user to the Blacklist.
    Only staff users can add users to the blacklist.
    """
    queryset = BlacklistedUser.objects.all()
    serializer_class = BlacklistSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request:
            return BlacklistedUser.objects.filter(added_by=self.request.user)
        else:
            BlacklistedUser.objects.none()

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)


class BlacklistedUserDetailAPIView(RetrieveUpdateDestroyAPIView):
    """
    get:
    Get details about a BlacklistedUser.
    Access restricted to staff users.
    delete:
    Delete a User from your Blacklist.
    patch:
    Update a BlacklistedUser.
    It's useful if you need to update the username of a User.
    put:
    Update a BlacklistedUser.
    It's useful if you need to update the username of a User.
    """
    queryset = BlacklistedUser.objects.all()
    serializer_class = BlacklistSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def perform_update(self, serializer):
        serializer.save(added_by=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            added_by=self.request.user,
            uid=self.kwargs['uid']
            )
