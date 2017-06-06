from django.contrib.auth import get_user_model

from rest_framework.serializers import (
    ModelSerializer, Serializer, CharField
    )
from rest_framework.fields import SerializerMethodField


class UserSerializer(ModelSerializer):
    uid = SerializerMethodField()

    def get_uid(self, obj):
        try:
            return obj.social_auth.filter(provider='openstreetmap').last().uid
        except AttributeError:
            return None

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'is_staff', 'is_active', 'uid', 'email')
        read_only_fields = ('username', 'is_staff', 'is_active', 'id', 'uid')


class SocialSignUpSerializer(Serializer):
    oauth_token = CharField()
    oauth_verifier = CharField()
    oauth_token_secret = CharField()
