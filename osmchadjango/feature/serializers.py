from rest_framework.fields import ReadOnlyField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ..changeset.serializers import (
    BasicSuspicionReasonsSerializer, BasicHarmfulReasonSerializer
    )
from .models import Feature


class FeatureSerializer(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    changeset = ReadOnlyField(source='changeset.id')
    reasons = BasicSuspicionReasonsSerializer(many=True)
    harmful_reasons = BasicHarmfulReasonSerializer(many=True)

    class Meta:
        model = Feature
        geo_field = 'geometry'
        exclude = ('comparator_version',)
