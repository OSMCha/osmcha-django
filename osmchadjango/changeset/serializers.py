from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, StringRelatedField
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


class ChangesetSerializerToStaff(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    reasons = StringRelatedField(many=True, read_only=True)
    harmful_reasons = StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Changeset
        geo_field = 'bbox'
        exclude = ('powerfull_editor', 'uid')


class ChangesetSerializer(ChangesetSerializerToStaff):
    reasons = SerializerMethodField()
    harmful_reasons = SerializerMethodField()

    def get_reasons(self, obj):
        return obj.reasons.filter(is_visible=True).values_list('name', flat=True)

    def get_harmful_reasons(self, obj):
        return obj.harmful_reasons.filter(
            is_visible=True
            ).values_list('name', flat=True)


class UserWhitelistSerializer(ModelSerializer):
    class Meta:
        model = UserWhitelist
        fields = ('whitelist_user',)
