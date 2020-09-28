from rest_framework.fields import ReadOnlyField, SerializerMethodField, CharField
from rest_framework.serializers import (
    ModelSerializer, ListSerializer, BaseSerializer, PrimaryKeyRelatedField,
    Serializer
    )
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Changeset, Tag, SuspicionReasons, UserWhitelist


class SuspicionReasonsSerializer(ModelSerializer):
    class Meta:
        model = SuspicionReasons
        fields = '__all__'


class BasicSuspicionReasonsSerializer(ModelSerializer):
    class Meta:
        model = SuspicionReasons
        fields = ('id', 'name')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class BasicTagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')


class ChangesetSerializerToStaff(GeoFeatureModelSerializer):
    """Serializer with all the Changeset model fields, except the
    'powerfull_editor'.
    """
    check_user = ReadOnlyField(source='check_user.name', default=None)
    reasons = BasicSuspicionReasonsSerializer(many=True, read_only=True)
    tags = BasicTagSerializer(many=True, read_only=True)
    features = ReadOnlyField(source='new_features', default=list)

    class Meta:
        model = Changeset
        geo_field = 'bbox'
        exclude = ('powerfull_editor', 'new_features')


class ChangesetSerializer(ChangesetSerializerToStaff):
    """Serializer with all the Changeset model fields, except the
    'powerfull_editor'. It doesn't list the SuspicionReasons and Tags whose
    'is_visible' field is False.
    """
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


class UserWhitelistSerializer(ModelSerializer):
    class Meta:
        model = UserWhitelist
        fields = ('whitelist_user',)


class ChangesetListStatsSerializer(ListSerializer):
    read_only = True

    def to_representation(self, data):
        data = Changeset.objects.filter(id__in=[i.id for i in data])
        checked_changesets = data.filter(checked=True)
        harmful_changesets = data.filter(harmful=True)

        if self.context['request'].user.is_staff:
            reasons = SuspicionReasons.objects.order_by('-name')
            tags = Tag.objects.order_by('-name')
        else:
            reasons = SuspicionReasons.objects.filter(
                is_visible=True
                ).order_by('-name')
            tags = Tag.objects.filter(is_visible=True).order_by('-name')

        reasons_list = [
            {'name': reason.name,
            'changesets': data.filter(reasons=reason).count(),
            'checked_changesets': checked_changesets.filter(reasons=reason).count(),
            'harmful_changesets': harmful_changesets.filter(reasons=reason).count(),
            }
            for reason in reasons
            ]
        tags_list = [
            {'name': tag.name,
            'changesets': data.filter(tags=tag).count(),
            'checked_changesets': checked_changesets.filter(tags=tag).count(),
            'harmful_changesets': harmful_changesets.filter(tags=tag).count(),
            }
            for tag in tags
            ]

        return {
            'changesets': data.count(),
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
        data = Changeset.objects.filter(id__in=[i.id for i in data])
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


# the following serializers are used only to validate input data in endpoints
# that check features/changesets or add/remove SuspicionReasons and Tags
class SuspicionReasonsChangesetSerializer(ModelSerializer):
    changesets = PrimaryKeyRelatedField(
        many=True,
        queryset=Changeset.objects.all(),
        help_text='List of changesets ids.'
        )

    class Meta:
        model = SuspicionReasons
        fields = ('changesets',)


class ChangesetTagsSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        help_text='List of tags ids'
        )

    class Meta:
        model = Changeset
        fields = ('tags',)


class ChangesetCommentSerializer(Serializer):
    comment = CharField(max_length=1000)
