import django_filters
from models import Changeset


class ChangesetFilter(django_filters.FilterSet):

    class Meta:
        model = Changeset
        fields = {
            # 'reasons': ['exact'],
            'create': ['gte'],
            'modify': ['gte'],
            'delete': ['gte'],
            'editor': ['icontains'],
            'comment': ['icontains'],
            'source': ['icontains'],
            'user': ['exact']
        }
