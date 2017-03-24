import json
import datetime

from django.views.generic import View, ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db import IntegrityError
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.exceptions import ValidationError
from django.conf import settings

import django_filters.rest_framework
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveAPIView, get_object_or_404,
    DestroyAPIView,
    )
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination

from osmchadjango.changeset import models as changeset_models

from .models import Feature
from .serializers import FeatureSerializer
from .filters import FeatureFilter


class StandardResultsSetPagination(GeoJsonPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class FeatureListAPIView(ListAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    pagination_class = StandardResultsSetPagination
    bbox_filter_field = 'geometry'
    filter_backends = (
        InBBoxFilter,
        django_filters.rest_framework.DjangoFilterBackend,
        )
    bbox_filter_include_overlapping = True
    filter_class = FeatureFilter


class FeatureListView(ListView):
    context_object_name = 'features'
    template_name = 'feature/feature_list.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super(FeatureListView, self).get_context_data(**kwargs)
        suspicion_reasons = changeset_models.SuspicionReasons.objects.all()
        get = self.request.GET.dict()
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
        queryset = Feature.objects.all().select_related('changeset')
        params = {}
        GET_dict = self.request.GET.dict()
        for key in GET_dict:
            if key in GET_dict and GET_dict[key] != '':
                params[key] = GET_dict[key]

        self.validate_params(params)

        if 'harmful' not in params:
            params['harmful'] = 'False'
        if 'checked' not in params:
            params['checked'] = 'All'
        if 'reasons' in params:
            if params['reasons'] == 'None':
                queryset = queryset.filter(reasons=None)
            else:
                queryset = queryset.filter(reasons=int(params['reasons']))
        if 'bbox' in params:
            bbox = Polygon.from_bbox((float(b) for b in params['bbox'].split(',')))
            queryset = queryset.filter(changeset__bbox__bboverlaps=bbox)

        queryset = FeatureFilter(params, queryset=queryset).qs

        if 'sort' in GET_dict and GET_dict['sort'] != '':
            queryset = queryset.order_by(GET_dict['sort'])
        else:
            queryset = queryset.order_by('-changeset__date')
        return queryset

    def validate_params(self, params):
        """FIXME: define error in except lines."""
        if 'reasons' in params.keys() and params['reasons'] != '':
            try:
                s = str(int(params['reasons']))
            except:
                raise ValidationError('reasons param must be a number')
        if 'bbox' in params.keys() and params['bbox'] != '':
            try:
                bbox = Polygon.from_bbox((float(b) for b in params['bbox'].split(',')))
            except:
                raise ValidationError('bbox param is invalid')


class FeatureDetailView(DetailView):
    """DetailView of Feature Model"""
    model = Feature
    context_object_name = 'feature'
    template_name = 'feature/feature_detail.html'

    def get_context_data(self, **kwargs):
        context = super(FeatureDetailView, self).get_context_data(**kwargs)
        new_geojson = json.dumps(self.object.geojson)
        if self.object.old_geojson:
            old_geojson = json.dumps(self.object.old_geojson)
        else:
            old_geojson = None
        context.update({
            'new_geojson': new_geojson,
            'old_geojson': old_geojson
            })
        return context

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']
        return get_object_or_404(Feature, changeset=changeset, url=url)


def get_geojson(request, changeset, slug):
    feature = get_object_or_404(Feature, url=slug)
    return JsonResponse(feature.geojson)


@csrf_exempt
def suspicion_create(request):
    """Create Suspicion Features. It nees to receive a key as get parameter in
    the url.
    """
    if request.method == 'POST':
        if ('key' in request.GET.dict().keys() and
                request.GET.dict()['key'] in settings.FEATURE_CREATION_KEYS):
            try:
                feature = json.loads(request.body)
            except:
                return HttpResponse("Improperly formatted JSON body", status=400)
            if 'properties' not in feature:
                return HttpResponse("Expecting a single GeoJSON feature", status=400)
            properties = feature.get('properties', {})
            changeset_id = properties.get('osm:changeset')

            if not changeset_id:
                return HttpResponse(
                    "Expecting 'osm:changeset' key in the GeoJSON properties",
                    status=400
                    )

            # Each changed feature should have a "suspicions" array of objects in its properties
            suspicions = properties.get('suspicions')
            reasons_texts = set()
            if suspicions:
                # Each "suspicion" object should two attributes: a "reason" describing
                # the suspicion and a "score" roughly describing the badness.
                # For now, I'm ignoring the score, but in the future it could be used
                # by osmcha to compute an overall changeset badness score
                for suspicion in suspicions:
                    reasons_texts.add(suspicion['reason'])

            reasons = set()
            for reason_text in reasons_texts:
                reason, created = changeset_models.SuspicionReasons.objects.get_or_create(
                    name=reason_text
                    )
                reasons.add(reason)

            feature['properties'].pop("suspicions")

            defaults = {
                "date": datetime.datetime.utcfromtimestamp(properties.get('osm:timestamp') / 1000),
                "uid": properties.get('osm:uid'),
                "is_suspect": True,
                }

            changeset, created = changeset_models.Changeset.objects.get_or_create(
                id=changeset_id,
                defaults=defaults
                )
            changeset.is_suspect = True
            try:
                changeset.reasons.add(*reasons)
            except IntegrityError:
                # This most often happens due to a race condition,
                # where two processes are saving to the same changeset
                # In this case, we can safely ignore this attempted DB Insert,
                # since what we wanted inserted has already been done through
                # a separate web request.
                print("Integrity error with changeset %s" % changeset_id)
            except ValueError as e:
                print("Value error with changeset %s" % changeset_id)
            changeset.save()

            try:
                geometry = GEOSGeometry(json.dumps(feature['geometry']))
            except:
                geometry = None
            defaults = {
                "geometry": geometry,
                "geojson": feature,
                "osm_id": properties['osm:id'],
                "osm_type": properties['osm:type'],
                "osm_version": properties['osm:version'],
                }
            suspicious_feature, created = Feature.objects.get_or_create(
                osm_id=properties['osm:id'],
                changeset=changeset,
                defaults=defaults
                )
            if 'oldVersion' in properties.keys():
                try:
                    suspicious_feature.old_geometry = GEOSGeometry(
                        json.dumps(properties['oldVersion']['geometry'])
                        )
                except:
                    suspicious_feature.old_geometry = None
                suspicious_feature.old_geojson = feature['properties'].pop("oldVersion")
            suspicious_feature.geojson = feature
            suspicious_feature.comparator_version = feature.get('comparator_version')
            suspicious_feature.url = suspicious_feature.osm_type + '-' + str(suspicious_feature.osm_id)
            try:
                suspicious_feature.reasons.add(*reasons)
            except IntegrityError:
                # This most often happens due to duplicates in dynamosm stream
                print("Integrity error with feature %s" % suspicious_feature.osm_id)
            except ValueError as e:
                print("Value error with feature %s" % suspicious_feature.osm_id)

            suspicious_feature.save()
            return JsonResponse({'success': "Suspicion created."})
        else:
            return HttpResponse(status=401)
    else:
        return HttpResponse(status=400)


class SetHarmfulFeature(SingleObjectMixin, View):
    model = Feature

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']

        return get_object_or_404(Feature, changeset=changeset, url=url)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.changeset.uid not in [i.uid for i in request.user.social_auth.all()]:
            return render(
                request,
                'feature/confirm_modify.html',
                {'feature': self.object, 'modification': _('harmful')}
                )
        else:
            return render(request, 'feature/not_allowed.html')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.changeset.uid not in [i.uid for i in request.user.social_auth.all()]:
            self.object.checked = True
            self.object.harmful = True
            self.object.check_user = request.user
            self.object.check_date = timezone.now()
            self.object.save()
            return HttpResponseRedirect(
                reverse(
                    'feature:detail',
                    args=[self.object.changeset, self.object.url]
                    )
                )
        else:
            return render(request, 'feature/not_allowed.html')


@csrf_exempt
def whitelist_user(request):
    '''View to mark a user as whitelisted.
    Accepts a single post parameter with the 'name' of the user to be white-listed.
    Whitelists that user for the currently logged in user.
    TODO: can this be converted to a CBV?
    '''
    name = request.POST.get('name', None)
    user = request.user
    if not user.is_authenticated():
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    if not name:
        return JsonResponse({'error': 'Needs name parameter'}, status=403)
    uw = changeset_models.UserWhitelist(user=user, whitelist_user=name)
    uw.save()
    return JsonResponse({'success': 'User %s has been white-listed' % name})


class SetGoodFeature(SingleObjectMixin, View):
    model = Feature

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']

        return get_object_or_404(Feature, changeset=changeset, url=url)

    def get(self, request, *args, **kwargs):
        if self.object.changeset.uid not in [i.uid for i in request.user.social_auth.all()]:
            return render(
                request,
                'feature/confirm_modify.html',
                {'feature': self.object, 'modification': _('good')}
                )
        else:
            return render(request, 'feature/not_allowed.html')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.changeset.uid not in [i.uid for i in request.user.social_auth.all()]:
            self.object.checked = True
            self.object.harmful = False
            self.object.check_user = request.user
            self.object.check_date = timezone.now()
            self.object.save()
            return HttpResponseRedirect(
                reverse('feature:detail', args=[self.object.changeset, self.object.url])
                )
        else:
            return render(request, 'feature/not_allowed.html')
