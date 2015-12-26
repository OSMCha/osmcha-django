from django.views.generic import View, ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone

from .models import Changeset


class ChangesetListView(ListView):
    """List Changesets"""
    queryset = Changeset.objects.filter(is_suspect=True).order_by('-date')
    context_object_name = 'changesets'
    paginate_by = 15


class ChangesetDetailView(DetailView):
    """DetailView of Changeset Model"""
    model = Changeset
    context_object_name = 'changeset'


class SetHarmfullChangeset(SingleObjectMixin, View):
    model = Changeset

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            return render(request, 'changeset/confirm_harmfull.html',
                {'changeset': self.object})
        else:
            return render(request, 'changeset/not_allowed.html')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.uid not in [i.uid for i in request.user.social_auth.all()]:
            self.object.harmfull = True
            self.object.check_user = request.user
            self.object.check_date = timezone.now()
            self.object.save()
            HttpResponseRedirect(reverse('changeset:detail', args=[self.object.pk]))
        else:
            return render(request, 'changeset/not_allowed.html')
