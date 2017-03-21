from django.contrib.gis.geos import Polygon

from django_filters import filters, FilterSet

from .models import Changeset


class ChangesetFilter(FilterSet):

    checked = filters.MethodFilter()
    harmful = filters.MethodFilter()
    is_suspect = filters.MethodFilter()
    usernames = filters.MethodFilter()
    checked_by = filters.MethodFilter()
    bbox = filters.MethodFilter()

    def filter_checked_by(self, queryset, value):
        if value:
            users = map(lambda x: x.strip(), value.split(','))
            return queryset.filter(check_user__username__in=users)
        return queryset

    def filter_bbox(self, queryset, value):
        if value:
            bbox = Polygon.from_bbox((float(b) for b in value.split(',')))
            return queryset.filter(bbox__bboverlaps=bbox)
        return queryset

    def filter_checked(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(checked=True)
        elif value == 'False':
            return queryset.filter(checked=False)
        return queryset

    def filter_harmful(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(harmful=True)
        elif value == 'False':
            return queryset.filter(harmful=False)
        return queryset

    def filter_is_suspect(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(is_suspect=True)
        return queryset

    def filter_usernames(self, queryset, value):
        if value:
            users_array = [t.strip() for t in value.split(',')]
            return queryset.filter(user__in=users_array)
        return queryset

    class Meta:
        model = Changeset
        fields = {
            # 'reasons': ['exact'],
            'create': ['gte', 'lte'],
            'modify': ['gte', 'lte'],
            'delete': ['gte', 'lte'],
            'date': ['gte', 'lte'],
            'editor': ['icontains'],
            'imagery_used': ['icontains'],
            'comment': ['icontains'],
            'source': ['icontains'],
            'harmful': [],
            'checked': [],
            'is_suspect': []
            }
