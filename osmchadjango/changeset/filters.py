from django.contrib.gis.geos import Polygon

from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter
from django_filters import filters
from rest_framework_gis.fields import GeometryField
from django_filters.widgets import BooleanWidget

from .models import Changeset


class ChangesetFilter(GeoFilterSet):
    """Allows to filter Changesets by any of its fields, except 'uuid' (id of
    OSM user). The 'reasons' and the 'harmful_reasons' fields can be filtered
    by the exact match (filter changesets that have all the search reasons) or
    by contains match (filter changesets that have any of the reasons).
    """
    geometry = GeometryFilter(
        name='bbox',
        lookup_expr='intersects',
        help_text="""Geospatial filter of changeset whose bbox intersects with
            another geometry. You can use any geometry type in this filter."""
        )
    checked_by = filters.CharFilter(
        name='check_user',
        method='filter_checked_by',
        help_text="""Filter changesets that were checked by a user. Use commas
            to search for more than one user."""
        )
    users = filters.CharFilter(
        name='user',
        method='filter_users',
        help_text="""Filter changesets created by a user. Use commas to search
            for more than one user."""
        )
    ids = filters.CharFilter(
        name='id',
        method='filter_ids',
        help_text="""Filter changesets by its ID. Use commas to search for more
            than one id."""
        )
    reasons = filters.CharFilter(
        name='reasons',
        method='filter_any_reasons',
        help_text="""Filter changesets that have one or more of the Suspicion
            Reasons. Inform the Suspicion Reasons ids separated by commas."""
        )
    all_reasons = filters.CharFilter(
        name='reasons',
        method='filter_all_reasons',
        help_text="""Filter changesets that have ALL the Suspicion Reasons of a
            list. Inform the Suspicion Reasons ids separated by commas."""
        )
    tags = filters.CharFilter(
        name='tags',
        method='filter_any_reasons',
        help_text="""Filter changesets that have one or more of the Tags. Inform
            the Tags ids separated by commas."""
        )
    all_tags = filters.CharFilter(
        name='tags',
        method='filter_all_reasons',
        help_text="""Filter changesets that have ALL the Tags of a list. Inform
            the Tags ids separated by commas."""
        )
    checked = filters.BooleanFilter(
        widget=BooleanWidget(),
        help_text="""Filter changesets that were checked or not. Use true/false,
            1/0 values."""
        )
    harmful = filters.BooleanFilter(
        widget=BooleanWidget(),
        help_text="""Filter changesets that were marked as harmful or not.
            Use true/false, 1/0 values."""
        )
    is_suspect = filters.BooleanFilter(
        widget=BooleanWidget(),
        help_text='Filter changesets that were considered suspect by OSMCHA.'
        )
    powerfull_editor = filters.BooleanFilter(
        widget=BooleanWidget(),
        help_text="""Filter changesets that were created using a software editor
            considered powerfull (those that allow to create, modify or delete
            data in a batch)."""
        )
    order_by = filters.CharFilter(
        name=None,
        method='order_queryset',
        help_text="""Order the Changesets by one of the following fields: id,
            date, check_date, create, modify or delete. Use a minus sign (-)
            before the field name to reverse the ordering. Default ordering is
            '-id'."""
        )
    hide_whitelist = filters.BooleanFilter(
        name=None,
        method='filter_whitelist',
        widget=BooleanWidget(),
        help_text="""If True, it will exclude the changesets created by the
            users that you whitelisted."""
        )
    area_lt = filters.CharFilter(
        name=None,
        method='filter_area_lt',
        help_text="""Filter changesets that have a bbox area lower than X times
            the area of your geospatial filter. For example, if the bbox or
            geometry you defined in your filter has an area of 1 degree and you
            set 'area_lt=2', it will filter the changesets whose bbox area is
            lower than 2 degrees."""
        )
    create__gte = filters.NumberFilter(
        name='create',
        lookup_expr='gte',
        help_text="""Filter changesets whose number of elements created are
            greater or equal a number."""
        )
    create__lte = filters.NumberFilter(
        name='create',
        lookup_expr='lte',
        help_text="""Filter changesets whose number of elements created are
            lower or equal a number."""
        )
    modify__gte = filters.NumberFilter(
        name='modify',
        lookup_expr='gte',
        help_text="""Filter changesets whose number of elements modified are
            greater or equal a number."""
        )
    modify__lte = filters.NumberFilter(
        name='modify',
        lookup_expr='lte',
        help_text="""Filter changesets whose number of elements modified are
            lower or equal a number."""
        )
    delete__gte = filters.NumberFilter(
        name='delete',
        lookup_expr='gte',
        help_text="""Filter changesets whose number of elements deleted are
            greater or equal a number."""
        )
    delete__lte = filters.NumberFilter(
        name='delete',
        lookup_expr='lte',
        help_text="""Filter changesets whose number of elements deleted are
            lower or equal a number."""
        )
    date__gte = filters.DateFilter(
        name='date',
        lookup_expr='gte',
        help_text='Filter changesets whose date is greater or equal a date.'
        )
    date__lte = filters.DateFilter(
        name='date',
        lookup_expr='lte',
        help_text='Filter changesets whose date is lower or equal a date.'
        )
    check_date__gte = filters.DateFilter(
        name='check_date',
        lookup_expr='gte',
        help_text='Filter changesets whose check_date is greater or equal a date.'
        )
    check_date__lte = filters.DateFilter(
        name='check_date',
        lookup_expr='lte',
        help_text='Filter changesets whose check_date is lower or equal a date.'
        )
    editor = filters.CharFilter(
        name='editor',
        lookup_expr='icontains',
        help_text="""Filter changesets by its editor field using the icontains
            lookup expression."""
        )
    comment = filters.CharFilter(
        name='comment',
        lookup_expr='icontains',
        help_text="""Filter changesets by its comment field using the icontains
            lookup expression."""
        )
    source = filters.CharFilter(
        name='source',
        lookup_expr='icontains',
        help_text="""Filter changesets by its source field using the icontains
            lookup expression."""
        )
    imagery_used = filters.CharFilter(
        name='imagery_used',
        lookup_expr='icontains',
        help_text="""Filter changesets by its imagery_used field using the
            icontains lookup expression."""
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
        lookup = '__'.join([name, 'name__in'])
        users = [t.strip() for t in value.split(',')]
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
        lookup = '__'.join([name, 'id', 'in'])
        values = [int(t) for t in value.split(',')]
        return queryset.filter(**{lookup: values}).distinct()

    def filter_all_reasons(self, queryset, name, value):
        lookup = '__'.join([name, 'id'])
        values = [int(t) for t in value.split(',')]
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

    def filter_area_lt(self, queryset, name, value):
        """This filter method was designed to exclude changesets that are much
        bigger than the filter area. For example, if you want only changesets
        that are lower than 5 times the filter area, you need to pass the value 5.
        """
        if 'geometry' in self.data.keys():
            try:
                filter_area = self.data['geometry'].area
            except AttributeError:
                filter_area = GeometryField().to_internal_value(
                    self.data['geometry']
                    ).area
            return queryset.filter(area__lt=float(value)*filter_area)
        elif 'in_bbox' in self.data.keys():
            try:
                filter_area = Polygon.from_bbox(
                    (float(n) for n in self.data['in_bbox'].split(','))
                    ).area
                return queryset.filter(area__lt=float(value)*filter_area)
            except ValueError:
                return queryset
        else:
            return queryset

    class Meta:
        model = Changeset
        fields = []
