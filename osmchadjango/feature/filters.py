from django_filters import FilterSet, filters
from django_filters.widgets import BooleanWidget

from .models import Feature


class FeatureFilter(FilterSet):

    checked = filters.BooleanFilter(widget=BooleanWidget())
    harmful = filters.BooleanFilter(widget=BooleanWidget())
    changeset_users = filters.CharFilter(name='changeset__user', method='filter_users')

    def filter_changeset_users(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        users_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: users_array})

    class Meta:
        model = Feature
        fields = {
            # 'reasons': ['exact'],
            'osm_version': ['gte', 'lte'],
            'changeset__date': ['gte', 'lte'],
            'changeset__editor': ['icontains'],
            'changeset__source': ['icontains'],
            }
