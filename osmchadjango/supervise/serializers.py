from django.core.urlresolvers import reverse

from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.fields import SerializerMethodField

from .models import AreaOfInterest


class AreaOfInterestSerializer(GeoFeatureModelSerializer):
    changesets_url = SerializerMethodField()

    class Meta:
        model = AreaOfInterest
        geo_field = 'geometry'
        exclude = ('user',)

    def get_changesets_url(self, obj):
        return reverse('supervise:aoi-list-changesets', args=[obj.id])
