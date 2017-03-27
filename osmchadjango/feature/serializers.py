from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ..changeset.serializers import (
    BasicSuspicionReasonsSerializer, BasicHarmfulReasonSerializer
    )
from .models import Feature


class FeatureSerializer(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    changeset = ReadOnlyField(source='changeset.id')
    date = ReadOnlyField(source='changeset.date')
    source = ReadOnlyField(source='changeset.source')
    imagery_used = ReadOnlyField(source='changeset.imagery_used')
    editor = ReadOnlyField(source='changeset.editor')
    comment = ReadOnlyField(source='changeset.comment')
    reasons = BasicSuspicionReasonsSerializer(many=True)
    harmful_reasons = BasicHarmfulReasonSerializer(many=True)
    osm_link = SerializerMethodField()

    class Meta:
        model = Feature
        geo_field = 'geometry'
        exclude = ('comparator_version',)

    def get_osm_link(self, obj):
        return obj.osm_link()
