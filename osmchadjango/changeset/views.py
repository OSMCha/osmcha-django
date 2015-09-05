from django.views.generic import ListView, DetailView

from .models import Changeset


class ChangesetListView(ListView):
    """List Changesets"""
    queryset = Changeset.objects.filter(is_suspect=True).order_by('-date')
    context_object_name = 'changesets'
    paginate_by = 15


class ChangesetDetailView(DetailView):
    model = Changeset
    context_object_name = 'changeset'
