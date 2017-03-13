from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer, StringRelatedField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Changeset


class ChangesetSerializer(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    reasons = StringRelatedField(many=True)
    harmful_reasons = StringRelatedField(many=True)

    class Meta:
        model = Changeset
        geo_field = 'bbox'
        exclude = ('powerfull_editor', 'uid')
