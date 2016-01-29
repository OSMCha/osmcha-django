from django.views.generic import View, ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

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
        context.update({
            'suspicion_reasons': suspicion_reasons
        })
        return context

    def get_queryset(self):
        queryset = Changeset.objects.filter(is_suspect=True).order_by('-date')
        queryset = ChangesetFilter(self.request.GET, queryset=queryset).qs
        # import pdb;pdb.set_trace()
        user = self.request.user
        if not user.is_authenticated():
            return queryset
        whitelisted_users = UserWhitelist.objects.filter(user=user).values('whitelist_user')
        return queryset.exclude(user__in=whitelisted_users)


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
        return JsonResponse({'error': 'Not authenciated'}, status=401)
    if not name:
        return JsonResponse({'error': 'Needs name parameter'}, status=403)
    uw = UserWhitelist(user=user, whitelist_user=name)
    uw.save()
    return JsonResponse({'success': 'User %s has been white-listed' % name})

