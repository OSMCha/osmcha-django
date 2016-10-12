import django_filters
from models import Feature
from django_filters import filters


class FeatureFilter(django_filters.FilterSet):

    checked = filters.MethodFilter()
    harmful = filters.MethodFilter()

    def filter_checked(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(checked=True)
        return queryset

    def filter_harmful(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(harmful=True)
        return queryset

    class Meta:
        model = Feature
        fields = {
            # 'reasons': ['exact'],
            'changeset__date': ['gte', 'lte'],
            'changeset__editor': ['icontains'],
            'changeset__source': ['icontains'],
            'changeset__user': ['exact'],
            'harmful': [],
            'checked': [],
        }

