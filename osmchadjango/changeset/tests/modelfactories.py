import json

from django.contrib.gis.geos import Polygon
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.gis.geos import Point, LineString

import factory

from ..models import Changeset, SuspicionReasons, UserWhitelist, Tag
from ...feature.models import Feature
from ...users.models import MappingTeam


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'user%d' % n)
    name = factory.Sequence(lambda n: 'user %d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@example.com' % obj.username)


class ChangesetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Changeset
        # create is a reserved word of DjangoModelFactory, so we need to rename
        # to be able to call it
        rename = {'form_create': 'create'}

    form_create = 20
    modify = 10
    delete = 3
    uid = '123123'
    user = 'test'
    editor = 'Potlatch 2'
    imagery_used = 'Mapbox'
    comments_count = 1
    powerfull_editor = False
    date = factory.LazyFunction(timezone.now)
    is_suspect = False
    bbox = Polygon([
        (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
        (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
        (-71.0646843, 44.2371354)
        ])
    metadata = {'changesets_count': 99, 'host': 'https://ideditor.netlify.app'}


class SuspectChangesetFactory(ChangesetFactory):
    form_create = 2000
    modify = 10
    delete = 30
    is_suspect = True


class HarmfulChangesetFactory(SuspectChangesetFactory):
    checked = True
    check_user = factory.SubFactory(UserFactory)
    check_date = factory.LazyFunction(timezone.now)
    harmful = True


class GoodChangesetFactory(HarmfulChangesetFactory):
    harmful = False
    checked = True
    check_user = factory.SubFactory(UserFactory)
    check_date = factory.LazyFunction(timezone.now)


class SuspicionReasonsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SuspicionReasons


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag


class UserWhitelistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserWhitelist


class FeatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feature

    changeset = factory.SubFactory(ChangesetFactory)
    osm_id = factory.Sequence(lambda n: n)
    osm_type = 'node'
    url = factory.Sequence(lambda n: 'node-%d' % n)
    osm_version = 1
    geometry = Point(42.1, 13.4)
    geojson = json.dumps(
        {'properties': {'osm:type': 'node', 'name': 'Test', 'building':'yes'}}
        )


class MappingTeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MappingTeam

    name = "Map Company"
    trusted = True
    created_by = factory.SubFactory(UserFactory)
    users = []
