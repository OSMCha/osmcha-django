from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.serializers import StringRelatedField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ..changeset.serializers import (
    BasicSuspicionReasonsSerializer, BasicTagSerializer
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
    reasons = StringRelatedField(many=True, read_only=True)
    tags = StringRelatedField(many=True, read_only=True)
    osm_link = SerializerMethodField()

    class Meta:
        model = Feature
        geo_field = 'geometry'
        exclude = ('comparator_version',)

    def get_osm_link(self, obj):
        return obj.osm_link()
