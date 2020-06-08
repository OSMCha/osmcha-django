# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.utils import IntegrityError
from django.conf import settings

import django_filters.rest_framework
from rest_framework import status
from rest_framework.decorators import (
    api_view, parser_classes, permission_classes, action, throttle_classes
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
from rest_framework.exceptions import APIException
import requests

from .models import Changeset, UserWhitelist, SuspicionReasons, Tag
from .filters import ChangesetFilter
from .serializers import (
    ChangesetSerializer, ChangesetSerializerToStaff, ChangesetStatsSerializer,
    ChangesetTagsSerializer, SuspicionReasonsChangesetSerializer,
    SuspicionReasonsSerializer, UserStatsSerializer, UserWhitelistSerializer,
    TagSerializer, ChangesetCommentSerializer
    )
from .tasks import ChangesetCommentAPI
from .throttling import NonStaffUserThrottle
from ..roulette_integration.utils import push_feature_to_maproulette
from ..roulette_integration.models import ChallengeIntegration


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
    permission_classes = (IsAuthenticated,)
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
    permission_classes = (IsAuthenticated,)
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

    @action(detail=True, methods=['post'])
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

    @action(detail=True, methods=['delete'])
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

    @action(detail=True, methods=['put'])
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

    @action(detail=True, methods=['put'])
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

    @action(detail=True, methods=['post'])
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

    @action(detail=True, methods=['delete'])
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


class WhitelistValidationException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'The user was already whitelisted by the request user.'


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
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise WhitelistValidationException()


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
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Changeset.objects.filter(uid=self.kwargs['uid'])


class ChangesetCommentAPIView(ModelViewSet):
    queryset = Changeset.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangesetCommentSerializer

    @action(detail=True, methods=['get'])
    def get_comments(self, request, pk):
        "List comments received by a changeset on the OpenStreetMap website."
        self.changeset = self.get_object()
        headers = {
            'apiKey': settings.OSM_COMMENTS_API_KEY,
            'Content-Type': 'application/json'
        }
        data = requests.get(
            'https://osm-comments-api.mapbox.com/api/v1/changesets/{}'.format(pk),
            headers=headers
            )
        if data.status_code != 200:
            return Response(
                data.json(),
                status=data.status_code
                )
        else:
            return Response(
                data.json().get('properties').get('comments'),
                status=status.HTTP_200_OK
                )

    @action(detail=True, methods=['post'])
    def post_comment(self, request, pk):
        "Post a comment to a changeset in the OpenStreetMap website."
        self.changeset = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if settings.ENABLE_POST_CHANGESET_COMMENTS:
                changeset_comment = ChangesetCommentAPI(
                    request.user,
                    self.changeset.id
                    )
                comment_response = changeset_comment.post_comment(
                    self.add_footer(serializer.data['comment'])
                    )
                if comment_response.get('success'):
                    return Response(
                        {'detail': 'Changeset comment posted succesfully.'},
                        status=status.HTTP_201_CREATED
                        )
                else:
                    return Response(
                        {'detail': 'Changeset comment failed.'},
                        status=status.HTTP_400_BAD_REQUEST
                        )
            else:
                return Response(
                    {'detail': 'Changeset comment is not enabled.'},
                    status=status.HTTP_403_FORBIDDEN
                    )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )

    def add_footer(self, message):
        status = ""
        if self.changeset.checked and self.changeset.harmful is not None:
            status = "#REVIEWED_{} #OSMCHA".format(
                'BAD' if self.changeset.harmful else 'GOOD'
                )
        return """{}
            ---
            {}
            Published using OSMCha: https://osmcha.org/changesets/{}
            """.format(message, status, self.changeset.id)


def validate_feature(feature):
    required_fields = ['changeset', 'osm_id', 'osm_type', 'reasons']
    missing_fields = [i for i in required_fields if i not in feature.keys()]
    # Check for missing required fields
    if len(missing_fields):
        message = 'Request data is missing the following fields {}.'.format(
            ', '.join(missing_fields)
            )
        return Response(
            {'detail': message},
            status=status.HTTP_400_BAD_REQUEST
            )
    # validate id and changeset fields
    try:
        int(feature.get('osm_id'))
        int(feature.get('changeset'))
    except ValueError:
        return Response(
            {'detail': 'osm_id or changeset values are not an integer.'},
            status=status.HTTP_400_BAD_REQUEST
            )
    # validate osm_type
    if feature.get('osm_type') not in ['node', 'way', 'relation']:
        return Response(
            {'detail': 'osm_type value should be "node", "way" or "relation".'},
            status=status.HTTP_400_BAD_REQUEST
            )
    # validate reasons
    if type(feature.get('reasons')) != list:
        return Response(
            {'detail': 'reasons value should be a list.'},
            status=status.HTTP_400_BAD_REQUEST
            )


def filter_primary_tags(feature):
    PRIMARY_TAGS = [
        'aerialway',
        'aeroway',
        'amenity',
        'barrier',
        'boundary',
        'building',
        'craft',
        'emergency',
        'geological',
        'highway',
        'historic',
        'landuse',
        'leisure',
        'man_made',
        'military',
        'natural',
        'office',
        'place',
        'power',
        'public_transport',
        'railway',
        'route',
        'shop',
        'tourism',
        'waterway'
    ]
    tags = feature.get('primary_tags', {})
    [
        tags.pop(key)
        for key in list(tags.keys())
        if key not in PRIMARY_TAGS
    ]
    return tags


@api_view(['POST'])
@throttle_classes((NonStaffUserThrottle,))
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated, IsAdminUser))
def add_feature(request):
    """Add suspicious Features to Changesets, storing it as a JSONField. The
    required fields are: 'osm_id', 'osm_type', 'reasons' and 'changeset'.
    The optional fields are 'version', 'name', 'primary_tags' and 'note'. Any
    other field will not be saved on the database. The permission to create
    features is limited to staff users.
    """
    feature = request.data

    changeset_fields_to_update = ['new_features']

    # validate data
    validation = validate_feature(feature)
    if validation:
        return validation

    # Get reasons to add to changeset and define if it changeset will be suspect
    suspicions = feature.get('reasons')
    has_visible_features = False
    if suspicions:
        reasons = set()
        for suspicion in suspicions:
            try:
                reason_id = int(suspicion)
                reason = SuspicionReasons.objects.get(id=reason_id)
                reasons.add(reason)
                if reason.is_visible:
                    has_visible_features = True
            except (ValueError, SuspicionReasons.DoesNotExist):
                reason, created = SuspicionReasons.objects.get_or_create(
                    name=suspicion
                    )
                reasons.add(reason)
                if reason.is_visible:
                    has_visible_features = True

    changeset_defaults = {
        'is_suspect': has_visible_features
        }

    changeset, created = Changeset.objects.get_or_create(
        id=feature.get('changeset'),
        defaults=changeset_defaults
        )

    if type(changeset.new_features) is not list:
        changeset.new_features = []
    elif len(changeset.new_features) > 0:
        for i, f in enumerate(changeset.new_features):
            if f['url'] == '{}-{}'.format(feature['osm_type'], feature['osm_id']):
                f['reasons'] = list(set(f['reasons'] + [i.id for i in reasons]))
                changeset.save(update_fields=changeset_fields_to_update)
                add_reasons_to_changeset(changeset, reasons)
                return Response(
                    {'detail': 'Feature added to changeset.'},
                    status=status.HTTP_200_OK
                    )

    fields_to_save = [
        'osm_id', 'version', 'reasons', 'name', 'note', 'primary_tags', 'url'
        ]
    feature['url'] = '{}-{}'.format(
        feature.get('osm_type'),
        feature.get('osm_id')
        )
    feature['reasons'] = [i.id for i in reasons]
    primary_tags = filter_primary_tags(feature)
    if len(primary_tags.items()):
        feature['primary_tags'] = primary_tags

    [feature.pop(k) for k in list(feature.keys()) if k not in fields_to_save]
    changeset.new_features.append(feature)

    if not changeset.is_suspect and has_visible_features:
        changeset.is_suspect = True
        changeset_fields_to_update.append('is_suspect')

    changeset.save(update_fields=changeset_fields_to_update)
    print(
        'Changeset {} {}'.format(
            changeset.id, 'created' if created else 'updated'
            )
        )
    add_reasons_to_changeset(changeset, reasons)
    return Response(
        {'detail': 'Feature added to changeset.'},
        status=status.HTTP_200_OK
        )


@api_view(['POST'])
@throttle_classes((NonStaffUserThrottle,))
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated, IsAdminUser))
def add_feature_v1(request):
    """Fallback View to add suspicious Features to Changesets. It supports the
    previous format of features that was generated by vandalism-dynamosm.
    """
    feature = {}
    feature['osm_id'] = request.data['properties']['osm:id']
    feature['changeset'] = request.data['properties']['osm:changeset']
    feature['osm_type'] = request.data['properties']['osm:type']
    feature['version'] = request.data['properties']['osm:version']
    feature['primary_tags'] = request.data['properties']
    feature['reasons'] = [
        i.get('reason') for i in request.data['properties'].get('suspicions')
        ]
    if request.data['properties'].get('name'):
        feature['name'] = request.data['properties'].get('name')
    if request.data['properties'].get('osmcha:note'):
        feature['note'] = request.data['properties'].get('osmcha:note')

    changeset_fields_to_update = ['new_features']

    # validate data
    validation = validate_feature(feature)
    if validation:
        return validation

    # Get reasons to add to changeset and define if it changeset will be suspect
    suspicions = feature.get('reasons')
    has_visible_features = False
    if suspicions:
        reasons = set()
        for suspicion in suspicions:
            try:
                reason_id = int(suspicion)
                reason = SuspicionReasons.objects.get(id=reason_id)
                reasons.add(reason)
                if reason.is_visible:
                    has_visible_features = True

            except (ValueError, SuspicionReasons.DoesNotExist):
                reason, created = SuspicionReasons.objects.get_or_create(
                    name=suspicion
                    )
                reasons.add(reason)
                if reason.is_visible:
                    has_visible_features = True

        challenges = ChallengeIntegration.objects.filter(
            active=True
            ).filter(reasons__in=reasons).distinct()
        for challenge in challenges:
            push_feature_to_maproulette(
                {
                    "type": "Feature",
                    "geometry": request.data.get('geometry'),
                    "properties": request.data.get('properties')
                },
                challenge.challenge_id,
                feature.get('osm_id'),
                [r.name for r in reasons]
                )

    changeset_defaults = {
        'is_suspect': has_visible_features
        }

    changeset, created = Changeset.objects.get_or_create(
        id=feature.get('changeset'),
        defaults=changeset_defaults
        )

    if type(changeset.new_features) is not list:
        changeset.new_features = []
    elif len(changeset.new_features) > 0:
        for i, f in enumerate(changeset.new_features):
            if f['url'] == '{}-{}'.format(feature['osm_type'], feature['osm_id']):
                f['reasons'] = list(set(f['reasons'] + [i.id for i in reasons]))
                changeset.save(update_fields=changeset_fields_to_update)
                add_reasons_to_changeset(changeset, reasons)
                return Response(
                    {'detail': 'Feature added to changeset.'},
                    status=status.HTTP_201_CREATED
                    )

    fields_to_save = [
        'osm_id', 'version', 'reasons', 'name', 'note', 'primary_tags', 'url'
        ]
    feature['url'] = '{}-{}'.format(
        feature.get('osm_type'),
        feature.get('osm_id')
        )
    feature['reasons'] = [i.id for i in reasons]
    primary_tags = filter_primary_tags(feature)
    if len(primary_tags.items()):
        feature['primary_tags'] = primary_tags

    [feature.pop(k) for k in list(feature.keys()) if k not in fields_to_save]
    changeset.new_features.append(feature)

    if not changeset.is_suspect and has_visible_features:
        changeset.is_suspect = True
        changeset_fields_to_update.append('is_suspect')

    changeset.save(update_fields=changeset_fields_to_update)
    print(
        'Changeset {} {}'.format(
            changeset.id, 'created' if created else 'updated'
            )
        )
    add_reasons_to_changeset(changeset, reasons)
    return Response(
        {'detail': 'Feature added to changeset.'},
        status=status.HTTP_201_CREATED
        )


def add_reasons_to_changeset(changeset, reasons):
    try:
        changeset.reasons.add(*reasons)
    except IntegrityError:
        # This most often happens due to a race condition,
        # where two processes are saving to the same changeset
        # In this case, we can safely ignore this attempted DB Insert,
        # since what we wanted inserted has already been done through
        # a separate web request.
        print('IntegrityError with changeset %s' % changeset.id)
    except ValueError:
        print('ValueError with changeset %s' % changeset.id)
