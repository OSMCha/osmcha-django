from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

import django_filters.rest_framework
from rest_framework import status
from rest_framework.decorators import (
    api_view, parser_classes, permission_classes, detail_route
    )
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveAPIView, get_object_or_404,
    DestroyAPIView
    )
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.viewsets import ModelViewSet
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_csv.renderers import CSVRenderer

from .models import Changeset, UserWhitelist, SuspicionReasons, Tag
from ..feature.models import Feature
from .filters import ChangesetFilter
from .serializers import (
    ChangesetSerializer, ChangesetSerializerToStaff, ChangesetStatsSerializer,
    ChangesetTagsSerializer, SuspicionReasonsChangesetSerializer,
    SuspicionReasonsFeatureSerializer, SuspicionReasonsSerializer,
    TagSerializer, UserStatsSerializer, UserWhitelistSerializer,
    )
from .throttling import NonStaffUserThrottle


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
    """List changesets. There are two ways of filtering changesets by
    geolocation. The first option is to use the 'geometry' filter field, which
    can receive any type of geometry as a GeoJson geometry string. The other is
    the 'in_bbox' parameter, which needs to receive the min Lat, min Lon, max
    Lat, max Lon values. Furthermore, we can filter the data by any other
    changeset property. The accepted response formats are JSON and CSV. The
    default pagination returns 50 objects by page.
    """

    queryset = Changeset.objects.all().select_related(
        'check_user'
        ).prefetch_related(
        'tags', 'reasons', 'features', 'features__reasons'
        ).exclude(user="")
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
    """Return the changesets that were not flagged as suspect. Accepts the same
    filter and pagination parameters of ChangesetListAPIView.
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
        if self.request and self.request.user.is_staff:
            return SuspicionReasons.objects.all()
        else:
            return SuspicionReasons.objects.filter(is_visible=True)


class AddRemoveChangesetReasonsAPIView(ModelViewSet):
    queryset = SuspicionReasons.objects.all()
    serializer_class = SuspicionReasonsChangesetSerializer
    permission_classes = (IsAdminUser,)

    @detail_route(methods=['post'])
    def add_reason_to_changesets(self, request, pk):
        """This endpoint allows us to add Suspicion Reasons to changesets in a
        batch. The use of this endpoint is restricted to staff users. The ids of
        the changesets must be sent as a list in the form data.
        """
        reason = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            reason.changesets.add(*serializer.data['changesets'])
            return Response(
                {'detail': 'Suspicion Reasons added to changesets.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )

    @detail_route(methods=['delete'])
    def remove_reason_from_changesets(self, request, pk):
        """This endpoint allows us to remove Suspicion Reasons from changesets
        in a batch. The use of this endpoint is restricted to staff users. The
        ids of the changesets must be sent as a list in the form data.
        """
        reason = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            reason.changesets.remove(*serializer.data['changesets'])
            return Response(
                {'detail': 'Suspicion Reasons removed from changesets.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )


class AddRemoveFeatureReasonsAPIView(ModelViewSet):
    queryset = SuspicionReasons.objects.all()
    serializer_class = SuspicionReasonsFeatureSerializer
    permission_classes = (IsAdminUser,)

    @detail_route(methods=['post'])
    def add_reason_to_features(self, request, pk):
        """This endpoint allows us to add Suspicion Reasons to features in a
        batch. The use of this endpoint is restricted to staff users. The ids of
        the features need to be sent as a list in the data form.
        """
        reason = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            reason.features.add(*serializer.data['features'])
            changesets = Changeset.objects.filter(
                features__in=serializer.data['features']
                )
            reason.changesets.add(*changesets)
            return Response(
                {'detail': 'Suspicion Reasons added to features.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )

    @detail_route(methods=['delete'])
    def remove_reason_from_features(self, request, pk):
        """This endpoint allows us to remove Suspicion Reasons from features
        in a batch. The use of this endpoint is restricted to staff users. The
        ids of the features must be sent as a list in the form data.
        """
        reason = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            reason.features.remove(*serializer.data['features'])
            changesets = Changeset.objects.filter(
                features__id__in=serializer.data['features']
                ).exclude(
                    features__reasons=reason
                )
            reason.changesets.remove(*changesets)

            features = Feature.objects.filter(
                id__in=serializer.data['features']
                )
            for feature in features:
                if feature.reasons.count() == 0:
                    feature.delete()

            return Response(
                {'detail': 'Suspicion Reasons removed from features.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )


class TagListAPIView(ListAPIView):
    """List Tags."""
    serializer_class = TagSerializer

    def get_queryset(self):
        if self.request and self.request.user.is_staff:
            return Tag.objects.all()
        else:
            return Tag.objects.filter(is_visible=True)


class CheckChangeset(ModelViewSet):
    queryset = Changeset.objects.all()
    serializer_class = ChangesetTagsSerializer
    permission_classes = (IsAuthenticated,)
    throttle_classes = [NonStaffUserThrottle]

    def update_changeset(self, changeset, request, harmful):
        """Update 'checked', 'harmful', 'check_user', 'check_date' fields of the
        changeset and return a 200 response"""
        changeset.checked = True
        changeset.harmful = harmful
        changeset.check_user = request.user
        changeset.check_date = timezone.now()
        changeset.save(
            update_fields=['checked', 'harmful', 'check_user', 'check_date']
            )
        return Response(
            {'detail': 'Changeset marked as {}.'.format('harmful' if harmful else 'good')},
            status=status.HTTP_200_OK
            )

    @detail_route(methods=['put'])
    def set_harmful(self, request, pk):
        """Mark a changeset as harmful. You can set the tags of the changeset by
        sending a list of tag ids inside a field named 'tags' in the request
        data.  If you don't want to set the 'tags', you don't need to send data,
        just make an empty PUT request.
        """
        changeset = self.get_object()
        if changeset.checked:
            return Response(
                {'detail': 'Changeset was already checked.'},
                status=status.HTTP_403_FORBIDDEN
                )
        if changeset.uid in request.user.social_auth.values_list('uid', flat=True):
            return Response(
                {'detail': 'User can not check his own changeset.'},
                status=status.HTTP_403_FORBIDDEN
                )
        if request.data:
            serializer = ChangesetTagsSerializer(data=request.data)
            if serializer.is_valid():
                changeset.tags.set(serializer.data['tags'])
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )
        return self.update_changeset(changeset, request, harmful=True)

    @detail_route(methods=['put'])
    def set_good(self, request, pk):
        """Mark a changeset as good. You can set the tags of the changeset by
        sending a list of tag ids inside a field named 'tags' in the request
        data.  If you don't want to set the 'tags', you don't need to send data,
        just make an empty PUT request.
        """
        changeset = self.get_object()
        if changeset.checked:
            return Response(
                {'detail': 'Changeset was already checked.'},
                status=status.HTTP_403_FORBIDDEN
                )
        if changeset.uid in request.user.social_auth.values_list('uid', flat=True):
            return Response(
                {'detail': 'User can not check his own changeset.'},
                status=status.HTTP_403_FORBIDDEN
                )
        if request.data:
            serializer = ChangesetTagsSerializer(data=request.data)
            if serializer.is_valid():
                changeset.tags.set(serializer.data['tags'])
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )
        return self.update_changeset(changeset, request, harmful=False)


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
            {'detail': 'Changeset is not checked.'},
            status=status.HTTP_403_FORBIDDEN
            )
    elif request.user == instance.check_user or request.user.is_staff:
        instance.checked = False
        instance.harmful = None
        instance.check_user = None
        instance.check_date = None
        instance.save(
            update_fields=['checked', 'harmful', 'check_user', 'check_date']
            )
        return Response(
            {'detail': 'Changeset marked as unchecked.'},
            status=status.HTTP_200_OK
            )
    else:
        return Response(
            {'detail': 'User does not have permission to uncheck this changeset.'},
            status=status.HTTP_403_FORBIDDEN
            )


class AddRemoveChangesetTagsAPIView(ModelViewSet):
    queryset = Changeset.objects.all()
    permission_classes = (IsAuthenticated,)
    # The serializer is not used in this view. It's here only to avoid errors
    # in docs schema generation.
    serializer_class = ChangesetStatsSerializer

    @detail_route(methods=['post'])
    def add_tag(self, request, pk, tag_pk):
        """Add a tag to a changeset. If the changeset is unchecked, any user can
        add tags. After the changeset got checked, only staff users and the user
        that checked it can add tags. The user that created the changeset can't
        add tags to it.
        """
        changeset = self.get_object()
        tag = get_object_or_404(Tag.objects.filter(for_changeset=True), pk=tag_pk)

        if changeset.uid in request.user.social_auth.values_list('uid', flat=True):
            return Response(
                {'detail': 'User can not add tags to his own changeset.'},
                status=status.HTTP_403_FORBIDDEN
                )
        if changeset.checked and (
            request.user != changeset.check_user and not request.user.is_staff):
            return Response(
                {'detail': 'User can not add tags to a changeset checked by another user.'},
                status=status.HTTP_403_FORBIDDEN
                )

        changeset.tags.add(tag)
        return Response(
            {'detail': 'Tag added to the changeset.'},
            status=status.HTTP_200_OK
            )

    @detail_route(methods=['delete'])
    def remove_tag(self, request, pk, tag_pk):
        """Remove a tag from a changeset. If the changeset is unchecked, any user
        can remove tags. After the changeset got checked, only staff users and
        the user that checked it can remove tags. The user that created the
        changeset can't remove tags from it.
        """
        changeset = self.get_object()
        tag = get_object_or_404(Tag.objects.all(), pk=tag_pk)

        if changeset.uid in request.user.social_auth.values_list('uid', flat=True):
            return Response(
                {'detail': 'User can not remove tags from his own changeset.'},
                status=status.HTTP_403_FORBIDDEN
                )
        if changeset.checked and (
            request.user != changeset.check_user and not request.user.is_staff):
            return Response(
                {'detail': 'User can not remove tags from a changeset checked by another user.'},
                status=status.HTTP_403_FORBIDDEN
                )

        changeset.tags.remove(tag)
        return Response(
            {'detail': 'Tag removed from the changeset.'},
            status=status.HTTP_200_OK
            )


class UserWhitelistListCreateAPIView(ListCreateAPIView):
    """
    get:
    List the users whitelisted by the request user.

    post:
    Add a user to the whitelist of the request user.
    """
    serializer_class = UserWhitelistSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request:
            return UserWhitelist.objects.filter(user=self.request.user)
        else:
            return UserWhitelist.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserWhitelistDestroyAPIView(DestroyAPIView):
    """Delete a user from the whitelist of the request user."""
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
    """Get stats about an OSM user in the OSMCHA history. It needs to receive
    the uid of the user in OSM.
    """
    serializer_class = UserStatsSerializer

    def get_queryset(self):
        return Changeset.objects.filter(uid=self.kwargs['uid'])
