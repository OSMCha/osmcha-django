import django_filters
from models import Changeset


class ChangesetFilter(django_filters.FilterSet):

    class Meta:
        model = Changeset
        fields = {
            # 'reasons': ['exact'],
            'create': ['gte', 'lte'],
            'modify': ['gte', 'lte'],
            'delete': ['gte', 'lte'],
            'editor': ['icontains'],
            'comment': ['icontains'],
            'source': ['icontains'],
            'user': ['exact'],
            'is_suspect': ['exact']
        }