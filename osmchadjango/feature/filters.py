import django_filters
from models import Feature
from django_filters import filters


class FeatureFilter(django_filters.FilterSet):

    checked = filters.MethodFilter()
    harmful = filters.MethodFilter()
    changeset__user = filters.MethodFilter()

    def filter_checked(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(checked=True)
        return queryset

    def filter_harmful(self, queryset, value):
        if value and value == 'True':
            return queryset.filter(harmful=True)
        return queryset

    def filter_changeset__user(self, queryset, value):
        if value:
            users_array = [t.strip() for t in value.split(',')]
            return queryset.filter(changeset__user__in=users_array)
        return queryset

    class Meta:
        model = Feature
        fields = {
            # 'reasons': ['exact'],
            'changeset__date': ['gte', 'lte'],
            'changeset__editor': ['icontains'],
            'changeset__source': ['icontains'],
            'harmful': [],
            'checked': [],
            'changeset__user': [],
        }

