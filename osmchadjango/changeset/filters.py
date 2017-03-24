from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter
from django_filters import filters
from django_filters.widgets import BooleanWidget

from .models import Changeset, UserWhitelist


class ChangesetFilter(GeoFilterSet):
    """Allows to filter Changesets by any of its fields, except 'uuid'
    (id of OSM user) and 'id' (changeset id). The 'reasons' and the 'harmful_reasons'
    fields can be filtered by the exact match (filter changesets that have all
    the search reasons) or by contains match (filter changesets that have any of
    the reasons).
    """
    bbox_overlaps = GeometryFilter(name='bbox', lookup_expr='overlaps')
    checked_by = filters.CharFilter(name='check_user', method='filter_checked_by')
    users = filters.CharFilter(name='user', method='filter_users')
    ids = filters.CharFilter(name='id', method='filter_ids')
    reasons = filters.CharFilter(name='reasons', method='filter_any_reasons')
    all_reasons = filters.CharFilter(name='reasons', method='filter_all_reasons')
    harmful_reasons = filters.CharFilter(
        name='harmful_reasons',
        method='filter_any_reasons'
        )
    all_harmful_reasons = filters.CharFilter(
        name='harmful_reasons',
        method='filter_all_reasons'
        )
    checked = filters.BooleanFilter(widget=BooleanWidget())
    harmful = filters.BooleanFilter(widget=BooleanWidget())
    is_suspect = filters.BooleanFilter(widget=BooleanWidget())
    powerfull_editor = filters.BooleanFilter(widget=BooleanWidget())
    order_by = filters.CharFilter(name=None, method='order_queryset')
    hide_whitelist = filters.BooleanFilter(
        name=None,
        method='filter_whitelist',
        widget=BooleanWidget(),
        )

    def filter_whitelist(self, queryset, name, value):
        if self.request.user.is_authenticated() and value:
            whitelist = self.request.user.whitelists.values_list(
                'whitelist_user',
                flat=True
                )
            return queryset.exclude(user__in=whitelist)
        else:
            return queryset

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

    def filter_any_reasons(self, queryset, name, value):
        lookup = '__'.join([name, 'name', 'in'])
        values = map(lambda x: x.strip(), value.split(','))
        return queryset.filter(**{lookup: values}).distinct()

    def filter_all_reasons(self, queryset, name, value):
        lookup = '__'.join([name, 'name'])
        values = map(lambda x: x.strip(), value.split(','))
        for term in values:
            queryset = queryset.filter(**{lookup: term})
        return queryset

    def order_queryset(self, queryset, name, value):
        allowed_fields = [
            'date', '-date', 'id', 'check_date', '-check_date', 'create',
            'modify', 'delete', '-create', '-modify', '-delete'
            ]
        if value in allowed_fields:
            return queryset.order_by(value)
        else:
            return queryset

    class Meta:
        model = Changeset
        fields = {
            'create': ['gte', 'lte'],
            'modify': ['gte', 'lte'],
            'delete': ['gte', 'lte'],
            'date': ['gte', 'lte'],
            'check_date': ['gte', 'lte'],
            'editor': ['exact', 'icontains'],
            'comment': ['exact', 'icontains'],
            'source': ['exact', 'icontains'],
            'imagery_used': ['exact', 'icontains'],
            }
