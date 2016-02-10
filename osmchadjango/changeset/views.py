from django.views.generic import View, ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import Q, Count

from .models import Changeset, UserWhitelist, SuspicionReasons
from django.views.decorators.csrf import csrf_exempt
from filters import ChangesetFilter


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
        if 'username' in params:
            params['user'] = params['username']
        if 'is_suspect' not in params:
            params['is_suspect'] = 'True'
        queryset = ChangesetFilter(params, queryset=queryset).qs
        if 'reasons' in params:
            queryset = queryset.filter(reasons=int(params['reasons']))
        # import pdb;pdb.set_trace()
        user = self.request.user
        if not user.is_authenticated():
            return queryset
        whitelisted_users = UserWhitelist.objects.filter(user=user).values('whitelist_user')
        users_on_multiple_whitelists = UserWhitelist.objects.annotate(count=Count('whitelist_user')).filter(count__gt=1).values('whitelist_user')
        queryset = queryset.exclude(Q(user__in=whitelisted_users) | Q(user__in=users_on_multiple_whitelists))
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
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            return render(
                request,
                'changeset/confirm_modify.html',
                {'changeset': self.object, 'modification': _('harmful')}
                )
        else:
            return render(request, 'changeset/not_allowed.html')

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
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            return render(
                request,
                'changeset/confirm_modify.html',
                {'changeset': self.object, 'modification': _('good')}
                )
        else:
            return render(request, 'changeset/not_allowed.html')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            self.object.checked = True
            self.object.harmful = False
            self.object.check_user = request.user
            self.object.check_date = timezone.now()
            self.object.save()
            good_changesets_by_user = Changeset.objects.filter(check_user=request.user).filter(user=self.object.user).filter(harmful=False).count()
            if good_changesets_by_user > 1:
                try:
                    uw = UserWhitelist(user=request.user, whitelist_user=self.object.user)
                    uw.save()
                except:
                    pass
            return HttpResponseRedirect(reverse('changeset:detail', args=[self.object.pk]))
        else:
            return render(request, 'changeset/not_allowed.html')


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
    total_checked = Changeset.objects.filter(checked=True).count()
    total_harmful = Changeset.objects.filter(harmful=True).count()
    users_whitelisted = UserWhitelist.objects.values('whitelist_user').distinct().count()
    context = {
        'checked': total_checked,
        'harmful': total_harmful,
        'users_whitelisted': users_whitelisted
    }
    return render(request, 'changeset/stats.html', context=context)

def all_whitelist_users(request):
    all_users = UserWhitelist.objects.values('whitelist_user').distinct()
    context = {
        'users': all_users
    }
    return render(request, 'changeset/all_whitelist_users.html', context=context)