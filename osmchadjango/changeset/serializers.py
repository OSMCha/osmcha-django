from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Changeset, HarmfulReason, SuspicionReasons, UserWhitelist


class SuspicionReasonsSerializer(ModelSerializer):
    class Meta:
        model = SuspicionReasons
        fields = '__all__'


class BasicSuspicionReasonsSerializer(ModelSerializer):
    class Meta:
        model = SuspicionReasons
        fields = ('name', 'is_visible')


class HarmfulReasonSerializer(ModelSerializer):
    class Meta:
        model = HarmfulReason
        fields = '__all__'


class BasicHarmfulReasonSerializer(ModelSerializer):
    class Meta:
        model = HarmfulReason
        fields = ('name', 'is_visible')


class ChangesetSerializer(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    reasons = BasicSuspicionReasonsSerializer(many=True)
    harmful_reasons = BasicHarmfulReasonSerializer(many=True)

    class Meta:
        model = Changeset
        geo_field = 'bbox'
        exclude = ('powerfull_editor', 'uid')


class ChangesetCSVSerializer(ModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    reasons = BasicSuspicionReasonsSerializer(many=True)
    harmful_reasons = BasicHarmfulReasonSerializer(many=True)

    class Meta:
        model = Changeset
        exclude = ('powerfull_editor', 'uid', 'bbox')


class UserWhitelistSerializer(ModelSerializer):
    class Meta:
        model = UserWhitelist
        fields = ('whitelist_user',)
