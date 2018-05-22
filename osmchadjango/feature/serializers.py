from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.serializers import (
    ModelSerializer, PrimaryKeyRelatedField
    )
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ..changeset.models import Tag
from ..changeset.serializers import (
    BasicTagSerializer, BasicSuspicionReasonsSerializer
    )
from .models import Feature


class FeatureSerializerToStaff(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.name', default=None)
    changeset = ReadOnlyField(source='changeset.id')
    date = ReadOnlyField(source='changeset.date')
    source = ReadOnlyField(source='changeset.source')
    imagery_used = ReadOnlyField(source='changeset.imagery_used')
    editor = ReadOnlyField(source='changeset.editor')
    comment = ReadOnlyField(source='changeset.comment')
    reasons = BasicSuspicionReasonsSerializer(many=True, read_only=True)
    tags = BasicTagSerializer(many=True, read_only=True)
    osm_link = SerializerMethodField()

    class Meta:
        model = Feature
        geo_field = 'geometry'
        exclude = ('comparator_version',)

    def get_osm_link(self, obj):
        return obj.osm_link()


class FeatureSerializer(FeatureSerializerToStaff):
    reasons = SerializerMethodField()
    tags = SerializerMethodField()

    def get_reasons(self, obj):
        return BasicSuspicionReasonsSerializer(
            obj.reasons.filter(is_visible=True),
            many=True,
            read_only=True
            ).data

    def get_tags(self, obj):
        return BasicTagSerializer(
            obj.tags.filter(is_visible=True),
            many=True,
            read_only=True
            ).data


class FeatureSerializerToUnauthenticated(FeatureSerializer):
    check_user = None

    class Meta:
        model = Feature
        geo_field = 'geometry'
        exclude = ('comparator_version', 'check_user')


class FeatureTagsSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())

    class Meta:
        model = Feature
        fields = ('tags',)
