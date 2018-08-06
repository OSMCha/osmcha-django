from django.urls import reverse

from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework_gis.fields import GeometryField
from rest_framework.fields import (
    SerializerMethodField, HiddenField, CurrentUserDefault, DateTimeField,
    ReadOnlyField
    )
from rest_framework.validators import ValidationError, UniqueTogetherValidator
from rest_framework.serializers import ModelSerializer

from .models import AreaOfInterest, BlacklistedUser


class AreaOfInterestSerializer(GeoFeatureModelSerializer):
    changesets_url = SerializerMethodField()
    user = HiddenField(default=CurrentUserDefault())
    geometry = GeometryField(read_only=True)

    class Meta:
        model = AreaOfInterest
        geo_field = 'geometry'
        fields = [
            'id', 'name', 'filters', 'geometry', 'date', 'changesets_url', 'user'
            ]
        validators = [
            UniqueTogetherValidator(
                queryset=AreaOfInterest.objects.all(),
                fields=('name', 'user')
                )
            ]

    def get_changesets_url(self, obj):
        return reverse('supervise:aoi-list-changesets', args=[obj.id])

    def validate(self, data):
        if data.get('filters') is None and data.get('geometry') is None:
            raise ValidationError(
                'Set a value to the filters field or to the geometry to be able to save the AoI'
                )
        return data


class AreaOfInterestAnonymousSerializer(AreaOfInterestSerializer):
    """Serializer to be used when an anonymous user access the AoI."""
    def to_representation(self, instance):
        data = super(
            AreaOfInterestAnonymousSerializer,
            self
            ).to_representation(instance)
        for key in ['users', 'uids', 'checked_by']:
            if key in data['properties']['filters'].keys():
                data['properties']['filters'].pop(key)

        return data


class BlacklistSerializer(ModelSerializer):
    date = DateTimeField(read_only=True)
    added_by = ReadOnlyField(source='added_by.username')

    class Meta:
        model = BlacklistedUser
        fields = ('uid', 'username', 'date', 'added_by')
