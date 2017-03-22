import datetime

from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.gis.geos import Polygon

from djqscsv import render_to_csv_response
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

from .models import Changeset, UserWhitelist, SuspicionReasons, HarmfulReason
from .filters import ChangesetFilter
from .serializers import (
    ChangesetSerializer, SuspicionReasonsSerializer, HarmfulReasonSerializer,
    UserWhitelistSerializer
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
    queryset = SuspicionReasons.objects.all()
    serializer_class = SuspicionReasonsSerializer


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
    if request.user == instance.check_user:
        if instance.checked is True:
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
                {'message': 'Changeset is not checked.'},
                status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'message': 'User does not have permission to uncheck this changeset.'},
            status=status.HTTP_403_FORBIDDEN
            )


class UserWhitelistListCreateAPIView(ListCreateAPIView):
    """List and create UserWhitelist model objects."""
    serializer_class = UserWhitelistSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserWhitelist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserWhitelistDestroyAPIView(DestroyAPIView):
    serializer_class = UserWhitelistSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'whitelist_user'

    def get_queryset(self):
        return UserWhitelist.objects.filter(user=self.request.user)


class ChangesetListView(ListView):
    """List Changesets"""
    # queryset = Changeset.objects.filter(is_suspect=True).order_by('-date')
    context_object_name = 'changesets'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super(ChangesetListView, self).get_context_data(**kwargs)
        suspicion_reasons = SuspicionReasons.objects.all()
        get = self.request.GET.dict()
        if 'is_suspect' not in get:
            get['is_suspect'] = 'True'
        if 'is_whitelisted' not in get:
            get['is_whitelisted'] = 'True'
        if 'harmful' not in get:
            get['harmful'] = 'False'
        if 'checked' not in get:
            get['checked'] = 'All'
        sorts = {
            '-date': 'Recent First',
            '-delete': 'Most Deletions First',
            '-modify': 'Most Modifications First',
            '-create': 'Most Creations First'
            }
        context.update({
            'suspicion_reasons': suspicion_reasons,
            'get': get,
            'sorts': sorts
            })
        return context

    def get_queryset(self):
        # queryset = Changeset.objects.filter(is_suspect=True).order_by('-date')
        queryset = Changeset.objects.all()
        params = {}
        GET_dict = self.request.GET.dict()
        for key in GET_dict:
            if key in GET_dict and GET_dict[key] != '':
                params[key] = GET_dict[key]
        self.validate_params(params)

        if 'is_suspect' not in params:
            params['is_suspect'] = 'True'
        if 'is_whitelisted' not in params:
            params['is_whitelisted'] = 'True'
        if 'harmful' not in params:
            params['harmful'] = None
        if 'checked' not in params:
            params['checked'] = 'All'
        queryset = ChangesetFilter(params, queryset=queryset).qs
        if 'reasons' in params:
            if params['reasons'] == 'None':
                queryset = queryset.filter(reasons=None)
            else:
                queryset = queryset.filter(reasons=int(params['reasons']))

        user = self.request.user

        if params['is_whitelisted'] == 'True' and user.is_authenticated():
            whitelisted_users = UserWhitelist.objects.filter(user=user).values('whitelist_user')
            queryset = queryset.exclude(Q(user__in=whitelisted_users))
        elif params['is_whitelisted'] == 'False' and user.is_authenticated():
            blacklisted_users = Changeset.objects.filter(harmful=True).values('user').distinct()
            queryset = queryset.filter(user__in=blacklisted_users)

        if 'sort' in GET_dict and GET_dict['sort'] != '':
            queryset = queryset.order_by(GET_dict['sort'])
        else:
            queryset = queryset.order_by('-date')
        return queryset

    def validate_params(self, params):
        """FIXME: define error in except lines."""
        if 'reasons' in params.keys() and params['reasons'] != '':
            try:
                s = str(int(params['reasons']))
            except:
                raise ValidationError('reasons param must be a number')
        if 'bbox' in params.keys() and params['bbox'] != '':
            print(params['bbox'])
            try:
                bbox = Polygon.from_bbox((float(b) for b in params['bbox'].split(',')))
            except:
                raise ValidationError('bbox param is invalid')

    def render_to_response(self, context, **response_kwargs):
        get_params = self.request.GET.dict()
        if 'render_csv' in get_params.keys() and get_params['render_csv'] == 'True':
            queryset = self.get_queryset()
            queryset = queryset.values(
                'id', 'user', 'editor', 'powerfull_editor', 'comment', 'source',
                'imagery_used', 'date', 'reasons', 'reasons__name', 'create',
                'modify', 'delete', 'bbox', 'is_suspect', 'harmful', 'checked',
                'check_user', 'check_date'
                )
            return render_to_csv_response(queryset)
        else:
            return super(ChangesetListView, self).render_to_response(context, **response_kwargs)


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
