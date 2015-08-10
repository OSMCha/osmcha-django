from django.views.generic import ListView

from .models import Changeset


class ChangesetListView(ListView):
    """List Changesets"""
    queryset = Changeset.objects.all().order_by('date')
    context_object_name = 'changesets'
    paginate_by = 15