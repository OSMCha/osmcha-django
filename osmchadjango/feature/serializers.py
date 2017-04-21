import json

from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.serializers import StringRelatedField, ModelSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Feature


class FeatureSerializerToStaff(GeoFeatureModelSerializer):
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


class FeatureSerializer(FeatureSerializerToStaff):
    reasons = SerializerMethodField()
    tags = SerializerMethodField()

    def get_reasons(self, obj):
        return obj.reasons.filter(is_visible=True).values_list('name', flat=True)

    def get_tags(self, obj):
        return obj.tags.filter(
            is_visible=True
            ).values_list('name', flat=True)


class FeatureSimpleSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = Feature
        fields = ('osm_id', 'url', 'name')

    def get_name(self, obj):
        try:
            return obj.geojson['properties']['name']
        except TypeError:
            try:
                return json.loads(obj.geojson)['properties']['name']
            except KeyError:
                return None
        except KeyError:
            return None
