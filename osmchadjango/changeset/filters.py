from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter
from django_filters import filters
from django_filters.widgets import BooleanWidget

from .models import Changeset


class ChangesetFilter(GeoFilterSet):
    bbox_overlaps = GeometryFilter(name='bbox', lookup_expr='overlaps')
    checked_by = filters.CharFilter(name='check_user', method='filter_checked_by')
    users = filters.CharFilter(name='user', method='filter_users')
    ids = filters.CharFilter(name='id', method='filter_ids')
    checked = filters.BooleanFilter(widget=BooleanWidget())
    harmful = filters.BooleanFilter(widget=BooleanWidget())
    is_suspect = filters.BooleanFilter(widget=BooleanWidget())
    powerfull_editor = filters.BooleanFilter(widget=BooleanWidget())

    def filter_checked_by(self, queryset, name, value):
        lookup = '__'.join([name, 'username__in'])
        users = map(lambda x: x.strip(), value.split(','))
        return queryset.filter(**{lookup: users})

    def filter_users(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        users_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: users_array})

    def filter_ids(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        values = [int(n) for n in value.split(',')]
        return queryset.filter(**{lookup: values})

    class Meta:
        model = Changeset
        fields = {
            # 'reasons': ['exact'],
            'create': ['gte', 'lte'],
            'modify': ['gte', 'lte'],
            'delete': ['gte', 'lte'],
            'date': ['gte', 'lte'],
            'check_date': ['gte', 'lte'],
            'editor': ['exact', 'icontains'],
            'comment': ['exact', 'icontains'],
            'source': ['exact', 'icontains'],
            }
