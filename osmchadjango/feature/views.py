from django.shortcuts import render
from django.views.generic import View, ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import Q, Count
from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import Polygon
from .models import Feature
from osmchadjango.changeset import models as changeset_models
from filters import FeatureFilter

# Create your views here.
from django.http import HttpResponse

import json
import datetime
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


class FeatureDetailView(DetailView):
    """DetailView of Changeset Model"""
    model = Feature
    context_object_name = 'feature'
    template_name = 'feature/feature_detail.html'

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']

        return get_object_or_404(Feature, changeset= changeset, url = url )



@csrf_exempt
def suspicion_create(request):
    if request.method=='POST':
        try:
            feature = json.loads(request.body)
        except:
            return HttpResponse("Improperly formatted JSON body", status=400)
        if 'properties' not in feature:
           return HttpResponse("Expecting a single GeoJSON feature", status=400)
        properties = feature.get('properties', {})
        changeset_id = properties.get('osm:changeset')

        if not changeset_id:
            return HttpResponse("Expecting 'osm:changeset' key in the GeoJSON properties", status=400)

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
            reason, created = changeset_models.SuspicionReasons.objects.get_or_create(name=reason_text)
            reasons.add(reason)

        feature['properties'].pop("suspicions")

        defaults = {
            "date": datetime.datetime.utcfromtimestamp(properties.get('osm:timestamp') / 1000),
            "uid": properties.get('osm:uid'),
            "is_suspect": True,
        }

        changeset, created = changeset_models.Changeset.objects.get_or_create(id=changeset_id, defaults=defaults)
        changeset.is_suspect = True
        changeset.reasons.add(*reasons)
        changeset.save()
        defaults = {
            "geometry": GEOSGeometry(json.dumps(feature['geometry'])),
            "geojson": json.dumps(feature),
            "osm_id": properties['osm:id'],
            "osm_type": properties['osm:type'],
            "osm_version": properties['osm:version'],
        }
        suspicious_feature, created = Feature.objects.get_or_create(id=properties['osm:id'], changeset=changeset, defaults=defaults)
        if 'oldVersion' in properties.keys():
            suspicious_feature.oldGeometry = GEOSGeometry(json.dumps(properties['oldVersion']['geometry']))
            suspicious_feature.oldGeojson= json.dumps(feature['properties'].pop("oldVersion"))
        suspicious_feature.geojson= json.dumps(feature)
        suspicious_feature.url = suspicious_feature.osm_type + '-' + str(suspicious_feature.osm_id)
        suspicious_feature.reasons.add(*reasons)
        suspicious_feature.save()
        return JsonResponse({'success': "Suspicion created."})
    else:
        return HttpResponse(400)


class SetHarmfulFeature(SingleObjectMixin, View):
    model = Feature

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']

        return get_object_or_404(Feature, changeset= changeset, url = url )

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
            return HttpResponseRedirect(reverse('feature:detail', args=[self.object.changeset, self.object.url]))
        else:
            return render(request, 'feature/not_allowed.html')

@csrf_exempt
def whitelist_user(request):
    '''
        View to mark a user as whitelisted.
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
    uw = UserWhitelist(user=user, whitelist_user=name)
    uw.save()
    return JsonResponse({'success': 'User %s has been white-listed' % name})

class SetGoodFeature(SingleObjectMixin, View):
    model = Feature

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']

        return get_object_or_404(Feature, changeset= changeset, url = url )

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
            return HttpResponseRedirect(reverse('feature:detail', args=[self.object.changeset, self.object.url]))
        else:
            return render(request, 'feature/not_allowed.html')
