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
from .models import Changeset, UserWhitelist, SuspicionReasons, SuspiciousFeature
from django.views.decorators.csrf import csrf_exempt
from filters import ChangesetFilter
from django.contrib.gis.geos import Polygon

import json
import datetime


class CheckedChangesetsView(ListView):
    context_object_name = 'changesets'
    paginate_by = 15
    template_name = 'changeset/changeset_list.html'

    def get_context_data(self, **kwargs):
        context = super(CheckedChangesetsView, self).get_context_data(**kwargs)
        context.update({
            'hide_filters': True,
            'search_title': _('Checked Changesets')
        })
        return context

    def get_queryset(self):
        from_date = self.request.GET.get('from', '')
        to_date = self.request.GET.get('to', datetime.datetime.now())
        if from_date and from_date != '':
            qset = Changeset.objects.filter(check_date__gte=from_date, check_date__lte=to_date)
        else:
            qset = Changeset.objects.all()
        return qset.filter(checked=True)


class HarmfulChangesetsView(ListView):
    context_object_name = 'changesets'
    paginate_by = 15
    template_name = 'changeset/changeset_list.html'

    def get_context_data(self, **kwargs):
        context = super(HarmfulChangesetsView, self).get_context_data(**kwargs)
        context.update({
            'hide_filters': True,
            'search_title': _('Harmful Changesets')
        })
        return context

    def get_queryset(self):
        from_date = self.request.GET.get('from', '')
        to_date = self.request.GET.get('to', datetime.datetime.now())
        if from_date and from_date != '':
            qset = Changeset.objects.filter(check_date__gte=from_date, check_date__lte=to_date)
        else:
            qset = Changeset.objects.all()
        return qset.filter(harmful=True)


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
        queryset = Changeset.objects.all().select_related('user_detail')
        params = {}
        GET_dict = self.request.GET.dict()
        for key in GET_dict:
            if key in GET_dict and GET_dict[key] != '':
                params[key] = GET_dict[key]
        if 'is_suspect' not in params:
            params['is_suspect'] = 'True'
        if 'is_whitelisted' not in params:
            params['is_whitelisted'] = 'True'
        if 'harmful' not in params:
            params['harmful'] = 'False'
        if 'checked' not in params:
            params['checked'] = 'All'
        queryset = ChangesetFilter(params, queryset=queryset).qs
        if 'reasons' in params:
            if params['reasons'] == 'None':
                queryset = queryset.filter(reasons=None)
            else:
                queryset = queryset.filter(reasons=int(params['reasons']))
        if 'bbox' in params:
            bbox = Polygon.from_bbox((float(b) for b in params['bbox'].split(',')))
            queryset = queryset.filter(bbox__bboverlaps=bbox)

        user = self.request.user

        if params['is_whitelisted'] == 'True' and user.is_authenticated():
            whitelisted_users = UserWhitelist.objects.filter(user=user).values('whitelist_user')
            users_on_multiple_whitelists = UserWhitelist.objects.values('whitelist_user').annotate(count=Count('whitelist_user')).filter(count__gt=1).values('whitelist_user')

            # users_on_multiple_whitelists = UserWhitelist.objects.annotate(count=Count('whitelist_user')).filter(count__gt=1).values('whitelist_user')
            queryset = queryset.exclude(Q(user__in=whitelisted_users) | Q(user__in=users_on_multiple_whitelists))
        elif params['is_whitelisted'] == 'False' and user.is_authenticated():
            blacklisted_users = Changeset.objects.filter(harmful=True).values('user').distinct()
            queryset = queryset.filter(user__in=blacklisted_users)

        if 'sort' in GET_dict and GET_dict['sort'] != '':
            queryset = queryset.order_by(GET_dict['sort'])
        else:
            queryset = queryset.order_by('-date')
        return queryset


class ChangesetDetailView(DetailView):
    """DetailView of Changeset Model"""
    model = Changeset
    context_object_name = 'changeset'


class SetHarmfulChangeset(SingleObjectMixin, View):
    model = Changeset

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(reverse('changeset:detail', args=[self.object.pk]))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            self.object.checked = True
            self.object.harmful = True
            self.object.check_user = request.user
            self.object.check_date = timezone.now()
            self.object.save()
            return HttpResponseRedirect(reverse('changeset:detail', args=[self.object.pk]))
        else:
            return render(request, 'changeset/not_allowed.html')


class SetGoodChangeset(SingleObjectMixin, View):
    model = Changeset

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(reverse('changeset:detail', args=[self.object.pk]))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            self.object.checked = True
            self.object.harmful = False
            self.object.check_user = request.user
            self.object.check_date = timezone.now()
            self.object.save()
            return HttpResponseRedirect(reverse('changeset:detail', args=[self.object.pk]))
        else:
            return render(request, 'changeset/not_allowed.html')

def undo_changeset_marking(request, pk):
    changeset_qs = Changeset.objects.filter(id=pk)
    changeset = changeset_qs[0]
    if request.user != changeset.check_user:
        return render(request, 'changeset/not_allowed.html')

    changeset.checked = False
    changeset.check_user = None
    changeset.check_date = None
    changeset.harmful = None
    changeset.save()
    return HttpResponseRedirect(reverse('changeset:detail', args=[pk]))

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

@csrf_exempt
def remove_from_whitelist(request):
    names = request.POST.get('names', None)
    user = request.user
    if not user.is_authenticated():
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    if not names:
        return JsonResponse({'error': 'Needs name parameter'}, status=403)
    names_array = names.split(',')
    UserWhitelist.objects.filter(user=user).filter(whitelist_user__in=names_array).delete()
    return JsonResponse({'success': 'Users removed from whitelist'})

def stats(request):
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', datetime.datetime.now())
    reviewer = request.GET.get('reviewer', '')
    if from_date:
        changesets_qset = Changeset.objects.filter(check_date__gte=from_date, check_date__lte=to_date)
    else:
        changesets_qset = Changeset.objects.all()
    if reviewer != '':
        changesets_qset = changesets_qset.filter(check_user__username=reviewer)
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

def all_whitelist_users(request):
    all_users = UserWhitelist.objects.values('whitelist_user').distinct()
    context = {
        'users': all_users
    }
    return render(request, 'changeset/all_whitelist_users.html', context=context)

def all_blacklist_users(request):
    blacklist_users = Changeset.objects.filter(harmful=True).values('user').distinct()
    context = {
        'users': blacklist_users
    }
    return render(request, 'changeset/all_blacklist_users.html', context=context)

def suspicious_feature_geojson(request, changeset_id, osm_id):
    suspicious_feature = get_object_or_404(SuspiciousFeature, changeset_id=changeset_id, osm_id=osm_id)
    geojson = suspicious_feature.geojson
    indented_geojson = json.dumps(json.loads(geojson), indent=2)
    return HttpResponse(indented_geojson, content_type='text/plain')

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
            reason, created = SuspicionReasons.objects.get_or_create(name=reason_text)
            reasons.add(reason)

        defaults = {
            "date": datetime.datetime.utcfromtimestamp(properties.get('osm:timestamp') / 1000),
            "uid": properties.get('osm:uid'),
            "is_suspect": True,
        }

        changeset, created = Changeset.objects.get_or_create(id=changeset_id, defaults=defaults)
        changeset.is_suspect = True
        changeset.reasons.add(*reasons)
        changeset.save()
        suspicious_feature = SuspiciousFeature(changeset=changeset)
        suspicious_feature.osm_id = properties['osm:id']
        suspicious_feature.geometry = GEOSGeometry(json.dumps(feature['geometry']))
        suspicious_feature.geojson = json.dumps(feature)
        suspicious_feature.save()
        suspicious_feature.reasons.add(*reasons)

        return JsonResponse({'success': "Suspicion created."})
    else:
        return HttpResponse(401)
