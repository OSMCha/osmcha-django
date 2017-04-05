from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import AreaOfInterest


class AreaOfInterestSimpleSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = AreaOfInterest
        geo_field = 'geometry'
        exclude = ('user',)
