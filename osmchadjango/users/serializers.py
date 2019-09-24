from django.contrib.auth import get_user_model

from rest_framework.serializers import (
    ModelSerializer, Serializer, CharField, SlugRelatedField
    )
from rest_framework.fields import ReadOnlyField
from rest_framework.fields import SerializerMethodField

from .models import MappingTeam


class UserSerializer(ModelSerializer):
    uid = SerializerMethodField()
    avatar = SerializerMethodField()
    username = SerializerMethodField()
    whitelists = SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='whitelist_user'
        )

    def get_uid(self, obj):
        try:
            return obj.social_auth.filter(provider='openstreetmap').last().uid
        except AttributeError:
            return None

    def get_avatar(self, obj):
        try:
            return obj.social_auth.filter(
                provider='openstreetmap'
                ).last().extra_data.get('avatar')
        except AttributeError:
            return None

    def get_username(self, obj):
        if obj.name:
            return obj.name
        else:
            return obj.username

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'uid', 'username', 'is_staff', 'is_active',  'email',
            'avatar', 'whitelists', 'message_good', 'message_bad',
            'comment_feature'
            )
        read_only_fields = ('username', 'is_staff', 'is_active', 'id', 'uid')


class SocialSignUpSerializer(Serializer):
    oauth_token = CharField()
    oauth_verifier = CharField()
    oauth_token_secret = CharField()


class MappingTeamSerializer(ModelSerializer):
    owner = ReadOnlyField(source='created_by.username', default=None)

    class Meta:
        model = MappingTeam
        fields = ('id', 'name', 'users', 'trusted', 'owner')
        read_only_fields = ('trusted', 'owner')
