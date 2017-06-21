from django.contrib.auth import get_user_model

from rest_framework.serializers import (
    ModelSerializer, Serializer, CharField
    )
from rest_framework.fields import SerializerMethodField


class UserSerializer(ModelSerializer):
    uid = SerializerMethodField()
    avatar = SerializerMethodField()

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

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'uid', 'username', 'is_staff', 'is_active',  'email', 'avatar'
            )
        read_only_fields = ('username', 'is_staff', 'is_active', 'id', 'uid')


class SocialSignUpSerializer(Serializer):
    oauth_token = CharField()
    oauth_verifier = CharField()
    oauth_token_secret = CharField()
