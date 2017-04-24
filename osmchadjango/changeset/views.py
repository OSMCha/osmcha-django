from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

import django_filters.rest_framework
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveAPIView, get_object_or_404,
    DestroyAPIView
    )
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_csv.renderers import CSVRenderer

from .models import Changeset, UserWhitelist, SuspicionReasons, Tag
from .filters import ChangesetFilter
from .serializers import (
    ChangesetSerializer, ChangesetSerializerToStaff, ChangesetStatsSerializer,
    SuspicionReasonsSerializer, TagSerializer,  UserWhitelistSerializer,
    UserStatsSerializer
    )


class StandardResultsSetPagination(GeoJsonPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class PaginatedCSVRenderer (CSVRenderer):
    results_field = 'features'

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        return super(PaginatedCSVRenderer, self).render(data, *args, **kwargs)


class ChangesetListAPIView(ListAPIView):
    """List changesets. The data can be filtered by any field, except 'id' and
    'uuid'. There are two ways of filtering changesets by geolocation. The first
    option is to use the 'geometry' filter field, which can receive any
    type of geometry. The other is the 'in_bbox' parameter, which needs to
    receive the min Lat, min Lon, max Lat, max Lon values. CSV and JSON are the
    accepted formats. The default pagination return 50 objects by page.
    """
    queryset = Changeset.objects.all().select_related(
        'check_user'
        ).prefetch_related('tags', 'reasons', 'features', 'features__reasons')
    pagination_class = StandardResultsSetPagination
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    bbox_filter_field = 'bbox'
    filter_backends = (
        InBBoxFilter,
        django_filters.rest_framework.DjangoFilterBackend,
        )
    bbox_filter_include_overlapping = True
    filter_class = ChangesetFilter

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ChangesetSerializerToStaff
        else:
            return ChangesetSerializer


class ChangesetDetailAPIView(RetrieveAPIView):
    """Return details of a Changeset."""
    queryset = Changeset.objects.all().select_related(
        'check_user'
        ).prefetch_related('tags', 'reasons')

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ChangesetSerializerToStaff
        else:
            return ChangesetSerializer


class SuspectChangesetListAPIView(ChangesetListAPIView):
    """Return the suspect changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    def get_queryset(self):
        return self.queryset.filter(is_suspect=True)


class NoSuspectChangesetListAPIView(ChangesetListAPIView):
    """Return the not suspect changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    def get_queryset(self):
        return self.queryset.filter(is_suspect=False)


class HarmfulChangesetListAPIView(ChangesetListAPIView):
    """Return the harmful changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    def get_queryset(self):
        return self.queryset.filter(harmful=True)


class NoHarmfulChangesetListAPIView(ChangesetListAPIView):
    """Return the not harmful changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    def get_queryset(self):
        return self.queryset.filter(harmful=False)


class CheckedChangesetListAPIView(ChangesetListAPIView):
    """Return the checked changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    def get_queryset(self):
        return self.queryset.filter(checked=True)


class UncheckedChangesetListAPIView(ChangesetListAPIView):
    """Return the unchecked changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    def get_queryset(self):
        return self.queryset.filter(checked=False)


class SuspicionReasonsListAPIView(ListAPIView):
    """List SuspicionReasons."""
    serializer_class = SuspicionReasonsSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return SuspicionReasons.objects.all()
        else:
            return SuspicionReasons.objects.filter(is_visible=True)


class TagListAPIView(ListAPIView):
    """List Tags."""
    serializer_class = TagSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Tag.objects.all()
        else:
            return Tag.objects.filter(is_visible=True)


@api_view(['PUT'])
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def set_harmful_changeset(request, pk):
    """Mark a changeset as harmful. The 'tags' field is optional and needs to be
    a list with the ids of the tags you want to add to the changeset. If you
    don't want to set the 'tags', you don't need to send data, just
    make an empty PUT request.
    """
    instance = get_object_or_404(Changeset.objects.all(), pk=pk)
    if instance.uid not in request.user.social_auth.values_list('uid', flat=True):
        if instance.checked is False:
            instance.checked = True
            instance.harmful = True
            instance.check_user = request.user
            instance.check_date = timezone.now()
            instance.save(
                update_fields=['checked', 'harmful', 'check_user', 'check_date']
                )
            if 'tags' in request.data.keys():
                ids = [int(i) for i in request.data.pop('tags')]
                tags = Tag.objects.filter(
                    id__in=ids
                    )
                instance.tags.set(tags)
            return Response(
                {'message': 'Changeset marked as harmful.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                {'message': 'Changeset could not be updated.'},
                status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'message': 'User does not have permission to update this changeset.'},
            status=status.HTTP_403_FORBIDDEN
            )


@api_view(['PUT'])
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def set_good_changeset(request, pk):
    """Mark a changeset as good. The 'tags' field is optional and needs to be
    a list with the ids of the tags you want to add to the changeset. If you
    don't want to set the 'tags', you don't need to send data, just
    make an empty PUT request.
    """
    instance = get_object_or_404(Changeset.objects.all(), pk=pk)
    if instance.uid not in request.user.social_auth.values_list('uid', flat=True):
        if instance.checked is False:
            instance.checked = True
            instance.harmful = False
            instance.check_user = request.user
            instance.check_date = timezone.now()
            instance.save(
                update_fields=['checked', 'harmful', 'check_user', 'check_date']
                )
            if 'tags' in request.data.keys():
                ids = [int(i) for i in request.data.pop('tags')]
                tags = Tag.objects.filter(
                    id__in=ids
                    )
                instance.tags.set(tags)
            return Response(
                {'message': 'Changeset marked as good.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                {'message': 'Changeset could not be updated.'},
                status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'message': 'User does not have permission to update this changeset.'},
            status=status.HTTP_403_FORBIDDEN
            )


@api_view(['PUT'])
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def uncheck_changeset(request, pk):
    """Mark a changeset as unchecked. You don't need to send data, just an empty
    PUT request."""
    instance = get_object_or_404(
        Changeset.objects.all().select_related('check_user'),
        pk=pk
        )
    if instance.checked is False:
        return Response(
            {'message': 'Changeset is not checked.'},
            status=status.HTTP_403_FORBIDDEN
            )
    elif request.user == instance.check_user:
        instance.checked = False
        instance.harmful = None
        instance.check_user = None
        instance.check_date = None
        instance.save(
            update_fields=['checked', 'harmful', 'check_user', 'check_date']
            )
        instance.tags.clear()
        return Response(
            {'message': 'Changeset marked as unchecked.'},
            status=status.HTTP_200_OK
            )
    else:
        return Response(
            {'message': 'User does not have permission to uncheck this changeset.'},
            status=status.HTTP_403_FORBIDDEN
            )


class UserWhitelistListCreateAPIView(ListCreateAPIView):
    """
    get:
    List your whitelisted users.

    post:
    Add a user to your whitelist.
    """
    serializer_class = UserWhitelistSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserWhitelist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserWhitelistDestroyAPIView(DestroyAPIView):
    """Delete a user from your whitelist."""
    serializer_class = UserWhitelistSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'whitelist_user'

    def get_queryset(self):
        return UserWhitelist.objects.filter(user=self.request.user)


class ChangesetStatsAPIView(ListAPIView):
    """Get stats about Changesets. It will return the total number of checked
    and harmful changesets, the number of users with harmful changesets and the
    number of checked and harmful changesets by Suspicion Reason and by Tag.
    It's possible to filter the changesets using the same filter parameters of
    the changeset list endpoint.
    """
    queryset = Changeset.objects.all().select_related(
        'check_user'
        ).prefetch_related('tags', 'reasons')
    serializer_class = ChangesetStatsSerializer
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    bbox_filter_field = 'bbox'
    filter_backends = (
        InBBoxFilter,
        django_filters.rest_framework.DjangoFilterBackend,
        )
    bbox_filter_include_overlapping = True
    filter_class = ChangesetFilter


class UserStatsAPIView(ListAPIView):
    """Get stats about a user in OSMCHA. You need to inform the uid of the user,
    so we can get the stats of all usernames he have used.
    """
    serializer_class = UserStatsSerializer

    def get_queryset(self):
        return Changeset.objects.filter(uid=self.kwargs['uid'])
