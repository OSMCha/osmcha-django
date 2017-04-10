from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter
from django_filters import filters
from django_filters.widgets import BooleanWidget

from .models import Feature


class FeatureFilter(GeoFilterSet):
    """Filter Feature model objects."""
    location = GeometryFilter(name='geometry', lookup_expr='intersects')
    checked = filters.BooleanFilter(widget=BooleanWidget())
    harmful = filters.BooleanFilter(widget=BooleanWidget())
    changeset_users = filters.CharFilter(
        name='changeset__user', method='filter_changeset_users'
        )
    checked_by = filters.CharFilter(
        name='check_user', method='filter_check_users'
        )
    reasons = filters.CharFilter(name='reasons', method='filter_any_reasons')
    all_reasons = filters.CharFilter(name='reasons', method='filter_all_reasons')
    tags = filters.CharFilter(
        name='tags',
        method='filter_any_reasons'
        )
    all_tags = filters.CharFilter(
        name='tags',
        method='filter_all_reasons'
        )
    order_by = filters.CharFilter(name=None, method='order_queryset')

    def filter_changeset_users(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        users_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: users_array})

    def filter_check_users(self, queryset, name, value):
        lookup = '__'.join([name, 'username', 'in'])
        users_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: users_array})

    def filter_any_reasons(self, queryset, name, value):
        lookup = '__'.join([name, 'name', 'in'])
        values = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: values}).distinct()

    def filter_all_reasons(self, queryset, name, value):
        lookup = '__'.join([name, 'name'])
        values = [t.strip() for t in value.split(',')]
        for term in values:
            queryset = queryset.filter(**{lookup: term})
        return queryset

    def order_queryset(self, queryset, name, value):
        allowed_fields = [
            '-id', 'id', '-osm_id', 'osm_id', 'changeset__date',
            '-changeset__date', 'changeset_id', 'check_date', '-check_date',
            ]
        if value in allowed_fields:
            return queryset.order_by(value)
        else:
            return queryset

    class Meta:
        model = Feature
        fields = {
            'osm_type': ['exact'],
            'osm_version': ['gte', 'lte'],
            'changeset__date': ['gte', 'lte'],
            'changeset__editor': ['icontains'],
            'changeset__source': ['icontains'],
            'check_date': ['gte', 'lte'],
            }
