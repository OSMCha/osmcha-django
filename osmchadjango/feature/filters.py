from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter
from django_filters import filters
from django_filters.widgets import BooleanWidget

from .models import Feature


class FeatureFilter(GeoFilterSet):
    """Filter Feature model objects."""
    geometry = GeometryFilter(
        name='geometry',
        lookup_expr='intersects',
        help_text="""Geospatial filter of features whose geometry intersects with
            another geometry. You can use any geometry type in this filter."""
        )
    checked = filters.BooleanFilter(
        widget=BooleanWidget(),
        help_text="""Filter features that were checked or not. Use true/false or
            1/0 values."""
        )
    changeset_checked = filters.BooleanFilter(
        name='changeset__checked',
        widget=BooleanWidget(),
        help_text="""Filter features whose changeset is checked or not. Use
            true/false or 1/0 values."""
        )
    harmful = filters.BooleanFilter(
        widget=BooleanWidget(),
        help_text="""Filter features that were marked as harmful or not harmful.
            Use true/false or 1/0 values."""
        )
    users = filters.CharFilter(
        name='changeset__user',
        method='filter_changeset_users',
        help_text="""Filter features whose last edit was made by a user. Use
            commas to search for more than one username."""
        )
    uids = filters.CharFilter(
        name='changeset__uid',
        method='filter_changeset_uid',
        help_text="""Filter features whose last edit was made by a user. Use
            commas to search for more than one user uid. The uid is a unique
            identifier of a OSM user."""
        )
    checked_by = filters.CharFilter(
        name='check_user',
        method='filter_check_users',
        help_text="""Filter features that were checked by a user. Use commas to
            search for more than one user."""
        )
    reasons = filters.CharFilter(
        name='reasons',
        method='filter_any_reasons',
        help_text="""Filter features that have one or more of the Suspicion
            Reasons. Inform the Suspicion Reasons ids separated by commas."""
        )
    all_reasons = filters.CharFilter(
        name='reasons',
        method='filter_all_reasons',
        help_text="""Filter features that have ALL the Suspicion Reasons of a
        list. Inform the Suspicion Reasons ids separated by commas."""
        )
    tags = filters.CharFilter(
        name='tags',
        method='filter_any_reasons',
        help_text="""Filter features that have one or more of the Tags. Inform
            the Tags ids separated by commas."""
        )
    all_tags = filters.CharFilter(
        name='tags',
        method='filter_all_reasons',
        help_text="""Filter features that have ALL the Tags of a list. Inform
            the Tags ids separated by commas."""
        )
    order_by = filters.CharFilter(
        name=None,
        method='order_queryset',
        help_text="""Order the Features by one of the following fields: id,
            osm_id, changeset__date, changeset_id or check_date. Use a minus
            sign (-) before the field name to reverse the ordering. Default
            ordering is '-changeset_id'."""
        )
    changeset_ids = filters.CharFilter(
        name='changeset__id',
        method='filter_changeset_ids',
        help_text="""Filter features by its changeset id. Send the ids separated
            by commas."""
        )
    osm_version__gte = filters.NumberFilter(
        name='osm_version',
        lookup_expr='gte',
        help_text="""Filter items whose osm_version is greater than or equal to
            a number."""
        )
    osm_version__lte = filters.NumberFilter(
        name='osm_version',
        lookup_expr='lte',
        help_text="""Filter items whose osm_version is lower than or equal to a
            number."""
        )
    osm_type = filters.CharFilter(
        name='osm_type',
        lookup_expr='exact',
        help_text="""Filter features by its osm_type. The value options are node,
            way or relation."""
        )
    date__gte = filters.DateTimeFilter(
        name='changeset__date',
        lookup_expr='gte',
        help_text="""Filter features whose changeset date is greater than or
            equal to a date or a datetime."""
        )
    date__lte = filters.DateTimeFilter(
        name='changeset__date',
        lookup_expr='lte',
        help_text="""Filter features whose changeset date is lower than or equal
            to a date or a datetime."""
        )
    check_date__gte = filters.DateTimeFilter(
        name='check_date',
        lookup_expr='gte',
        help_text="""Filter features whose check_date is greater than or equal
            to a date or a datetime."""
        )
    check_date__lte = filters.DateTimeFilter(
        name='check_date',
        lookup_expr='lte',
        help_text="""Filter features whose check_date is lower than or equal to
            a date or a datetime."""
        )
    editor = filters.CharFilter(
        name='changeset__editor',
        lookup_expr='icontains',
        help_text="""Filter features that were created or last modified with a
            software editor. The lookup expression used is 'icontains', so a
            query for 'josm' will get features created or last modified with
            all JOSM versions.
            """
        )

    def filter_changeset_users(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        users_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: users_array})

    def filter_changeset_uid(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        uids_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: uids_array})

    def filter_check_users(self, queryset, name, value):
        lookup = '__'.join([name, 'name', 'in'])
        check_users_array = [t.strip() for t in value.split(',')]
        return queryset.filter(**{lookup: check_users_array})

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
            '-id', 'id', '-osm_id', 'osm_id', 'changeset__date',
            '-changeset__date', 'changeset_id', 'check_date', '-check_date',
            ]
        if value in allowed_fields:
            return queryset.order_by(value)
        else:
            return queryset

    def filter_changeset_ids(self, queryset, name, value):
        lookup = '__'.join([name, 'in'])
        values = [int(t) for t in value.split(',')]
        return queryset.filter(**{lookup: values})

    class Meta:
        model = Feature
        fields = []
