from datetime import datetime

from django.contrib.gis.geos import Polygon
from django.contrib.auth import get_user_model

import factory

from ..models import Changeset, SuspicionReasons, UserWhitelist


class ChangesetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Changeset

    uid = '123123'
    user = 'test'
    editor = 'Potlatch 2'
    powerfull_editor = False
    date = factory.LazyFunction(datetime.now)
    is_suspect = False
    bbox = Polygon([
        (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
        (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
        (-71.0646843, 44.2371354)
        ])


class SuspectChangesetFactory(ChangesetFactory):
    create = 2000,
    modify = 10,
    delete = 30,
    is_suspect = True,


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()


class SuspicionReasonsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SuspicionReasons


class UserWhitelistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserWhitelist
