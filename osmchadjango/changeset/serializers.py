from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.serializers import (
    ModelSerializer, StringRelatedField, ListSerializer, BaseSerializer
    )
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ..feature.serializers import FeatureSimpleSerializer
from .models import Changeset, Tag, SuspicionReasons, UserWhitelist


class SuspicionReasonsSerializer(ModelSerializer):
    class Meta:
        model = SuspicionReasons
        fields = '__all__'


class BasicSuspicionReasonsSerializer(ModelSerializer):
    class Meta:
        model = SuspicionReasons
        fields = ('name', 'is_visible')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class BasicTagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name', 'is_visible')


class ChangesetSerializerToStaff(GeoFeatureModelSerializer):
    check_user = ReadOnlyField(source='check_user.username')
    reasons = StringRelatedField(many=True, read_only=True)
    tags = StringRelatedField(many=True, read_only=True)
    features = FeatureSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Changeset
        geo_field = 'bbox'
        exclude = ('powerfull_editor',)


class ChangesetSerializer(ChangesetSerializerToStaff):
    reasons = SerializerMethodField()
    tags = SerializerMethodField()

    def get_reasons(self, obj):
        return obj.reasons.filter(is_visible=True).values_list('name', flat=True)

    def get_tags(self, obj):
        return obj.tags.filter(
            is_visible=True
            ).values_list('name', flat=True)


class UserWhitelistSerializer(ModelSerializer):
    class Meta:
        model = UserWhitelist
        fields = ('whitelist_user',)


class ChangesetListStatsSerializer(ListSerializer):
    read_only = True

    def to_representation(self, data):
        checked_changesets = data.filter(checked=True)
        harmful_changesets = data.filter(harmful=True)

        if self.context['request'].user.is_staff:
            reasons = SuspicionReasons.objects.order_by('-name')
            tags = Tag.objects.order_by('-name')
        else:
            reasons = SuspicionReasons.objects.filter(is_visible=True).order_by('-name')
            tags = Tag.objects.filter(is_visible=True).order_by('-name')

        reasons_list = [
            {'name': reason.name,
            'checked_changesets': checked_changesets.filter(reasons=reason).count(),
            'harmful_changesets': harmful_changesets.filter(reasons=reason).count(),
            }
            for reason in reasons
            ]
        tags_list = [
            {'name': tag.name,
            'checked_changesets': checked_changesets.filter(tags=tag).count(),
            'harmful_changesets': harmful_changesets.filter(tags=tag).count(),
            }
            for tag in tags
            ]

        return {
            'checked_changesets': checked_changesets.count(),
            'harmful_changesets': harmful_changesets.count(),
            'users_with_harmful_changesets': harmful_changesets.values_list(
                'user', flat=True
                ).distinct().count(),
            'reasons': reasons_list,
            'tags': tags_list
            }

    @property
    def data(self):
        return super(ListSerializer, self).data


class ChangesetStatsSerializer(BaseSerializer):
    class Meta:
        list_serializer_class = ChangesetListStatsSerializer


class UserStatsListSerializer(ListSerializer):
    read_only = True

    def to_representation(self, data):
        checked_changesets = data.filter(checked=True)
        harmful_changesets = data.filter(harmful=True)

        return {
            'changesets_in_osmcha': data.count(),
            'checked_changesets': checked_changesets.count(),
            'harmful_changesets': harmful_changesets.count()
            }

    @property
    def data(self):
        return super(ListSerializer, self).data


class UserStatsSerializer(BaseSerializer):
    class Meta:
        list_serializer_class = UserStatsListSerializer
