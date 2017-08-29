from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from osmchadjango.changeset.models import Changeset
from .models import Priority


class PriorityCreationSerializer(ModelSerializer):

    class Meta:
        model = Priority
        fields = ('changeset',)
