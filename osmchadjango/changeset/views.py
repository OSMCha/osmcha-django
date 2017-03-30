import datetime

from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

import django_filters.rest_framework
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveAPIView, get_object_or_404,
    DestroyAPIView,
    )
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_csv.renderers import CSVRenderer

from .models import Changeset, UserWhitelist, SuspicionReasons, HarmfulReason
from .filters import ChangesetFilter
from .serializers import (
    ChangesetSerializer, ChangesetCSVSerializer, SuspicionReasonsSerializer,
    HarmfulReasonSerializer, UserWhitelistSerializer
    )


class StandardResultsSetPagination(GeoJsonPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class ChangesetListAPIView(ListAPIView):
    """List changesets. The data can be filtered by any field, except 'id' and
    'uuid'. There are two ways of filtering changesets by geolocation. The first
    option is to use the 'bbox_overlaps' filter field, which can receive any
    type of geometry. The other is the 'in_bbox' parameter, which needs to
    receive the min Lat, min Lon, max Lat, max Lon values.

    sub-urls:
    We have some sub-urls to make it easy to access filtered data: They are:

    """
    queryset = Changeset.objects.all()
    serializer_class = ChangesetSerializer
    pagination_class = StandardResultsSetPagination
    bbox_filter_field = 'bbox'
    filter_backends = (
        InBBoxFilter,
        django_filters.rest_framework.DjangoFilterBackend,
        )
    bbox_filter_include_overlapping = True
    filter_class = ChangesetFilter


class ChangesetCSVListAPIView(ListAPIView):
    """List changesets and return in the CSV format. The data can be filtered by any field, except 'id' and
    'uuid'. There are two ways of filtering changesets by geolocation. The first
    option is to use the 'bbox_overlaps' filter field, which can receive any
    type of geometry. The other is the 'in_bbox' parameter, which needs to
    receive the min Lat, min Lon, max Lat, max Lon values.
    """
    queryset = Changeset.objects.all()
    serializer_class = ChangesetCSVSerializer
    renderer_classes = (CSVRenderer,)
    bbox_filter_field = 'bbox'
    filter_backends = (
        InBBoxFilter,
        django_filters.rest_framework.DjangoFilterBackend,
        )
    bbox_filter_include_overlapping = True
    filter_class = ChangesetFilter


class ChangesetDetailAPIView(RetrieveAPIView):
    """Return details of a Changeset."""
    queryset = Changeset.objects.all()
    serializer_class = ChangesetSerializer


class SuspectChangesetListAPIView(ChangesetListAPIView):
    """Return the suspect changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    queryset = Changeset.objects.filter(is_suspect=True)


class NoSuspectChangesetListAPIView(ChangesetListAPIView):
    """Return the not suspect changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    queryset = Changeset.objects.filter(is_suspect=False)


class HarmfulChangesetListAPIView(ChangesetListAPIView):
    """Return the harmful changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    queryset = Changeset.objects.filter(harmful=True)


class NoHarmfulChangesetListAPIView(ChangesetListAPIView):
    """Return the not harmful changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    queryset = Changeset.objects.filter(harmful=False)


class CheckedChangesetListAPIView(ChangesetListAPIView):
    """Return the checked changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    queryset = Changeset.objects.filter(checked=True)


class UncheckedChangesetListAPIView(ChangesetListAPIView):
    """Return the unchecked changesets. Accepts the same filter and pagination
    parameters of ChangesetListAPIView.
    """
    queryset = Changeset.objects.filter(checked=False)


class SuspicionReasonsListAPIView(ListAPIView):
    """List SuspicionReasons."""
    serializer_class = SuspicionReasonsSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return SuspicionReasons.objects.all()
        else:
            return SuspicionReasons.objects.filter(is_visible=True)


class HarmfulReasonListAPIView(ListAPIView):
    """List HarmfulReasons."""
    queryset = HarmfulReason.objects.all()
    serializer_class = HarmfulReasonSerializer


@api_view(['PUT'])
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def set_harmful_changeset(request, pk):
    """Mark a changeset as harmful. The 'harmful_reasons'
    field is optional and needs to be a list with the ids of the reasons. If you
    don't want to set the 'harmful_reasons', you don't need to send data, just
    make an empty PUT request.
    """
    instance = get_object_or_404(Changeset.objects.all(), pk=pk)
    if instance.uid not in [i.uid for i in request.user.social_auth.all()]:
        if instance.checked is False:
            instance.checked = True
            instance.harmful = True
            instance.check_user = request.user
            instance.check_date = timezone.now()
            instance.save()
            if 'harmful_reasons' in request.data.keys():
                ids = [int(i) for i in request.data.pop('harmful_reasons')]
                harmful_reasons = HarmfulReason.objects.filter(
                    id__in=ids
                    )
                for reason in harmful_reasons:
                    reason.changesets.add(instance)
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
def set_good_changeset(request, pk):
    """Mark a changeset as good. You don't need to send data, just an empty
    PUT request.
    """
    instance = get_object_or_404(Changeset.objects.all(), pk=pk)
    if instance.uid not in [i.uid for i in request.user.social_auth.all()]:
        if instance.checked is False:
            instance.checked = True
            instance.harmful = False
            instance.check_user = request.user
            instance.check_date = timezone.now()
            instance.save()
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
    instance = get_object_or_404(Changeset.objects.all(), pk=pk)
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
        instance.save()
        instance.harmful_reasons.clear()
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


def stats(request):
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', datetime.datetime.now())
    reviewer = request.GET.get('reviewer', '')
    if from_date:
        changesets_qset = Changeset.objects.filter(check_date__gte=from_date, check_date__lte=to_date)
    else:
        changesets_qset = Changeset.objects.all()

    changesets_qset = ChangesetFilter(request.GET, queryset=changesets_qset).qs

    total_checked = changesets_qset.filter(checked=True).count()
    total_harmful = changesets_qset.filter(harmful=True).count()
    users_whitelisted = UserWhitelist.objects.values('whitelist_user').distinct().count()
    users_blacklisted = changesets_qset.filter(harmful=True).values('user').distinct().count()

    counts = {}
    for reason in SuspicionReasons.objects.all():
        counts[reason.name] = {}
        counts[reason.name]['id'] = reason.id
        counts[reason.name]['checked'] = changesets_qset.filter(reasons=reason, checked=True).count()
        counts[reason.name]['harmful'] = changesets_qset.filter(reasons=reason, harmful=True).count()

    counts['None'] = {}
    counts['None']['id'] = 'None'
    counts['None']['checked'] = changesets_qset.filter(reasons=None, checked=True).count()
    counts['None']['harmful'] = changesets_qset.filter(reasons=None, harmful=True).count()

    context = {
        'checked': total_checked,
        'harmful': total_harmful,
        'users_whitelisted': users_whitelisted,
        'users_blacklisted': users_blacklisted,
        'counts': counts,
        'get': request.GET.dict()
        }
    return render(request, 'changeset/stats.html', context=context)
