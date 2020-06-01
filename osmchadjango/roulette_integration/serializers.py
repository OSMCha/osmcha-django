from rest_framework.fields import HiddenField, CurrentUserDefault, ReadOnlyField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from ..changeset.serializers import SuspicionReasonsSerializer
from .models import ChallengeIntegration


class ChallengeIntegrationSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())
    owner = ReadOnlyField(source='user.username', default=None)

    # def create(self, validated_data):
    #     import ipdb; ipdb.set_trace()
    #     reasons_data = [i.get('id') for i in validated_data.pop('reasons')]
    #     obj = ChallengeIntegration.objects.create(**validated_data)

    class Meta:
        model = ChallengeIntegration
        fields = ['id', 'challenge_id', 'reasons', 'user', 'active', 'created', 'owner']
        read_only_fields = ('created', 'owner')
