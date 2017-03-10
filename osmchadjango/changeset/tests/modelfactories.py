from datetime import datetime

from django.contrib.gis.geos import Polygon
from django.contrib.auth import get_user_model

import factory

from ..models import Changeset, SuspicionReasons, UserWhitelist, HarmfulReason


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'user%d' % n)
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
    powerfull_editor = False
    date = factory.LazyFunction(datetime.now)
    is_suspect = False
    bbox = Polygon([
        (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
        (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
        (-71.0646843, 44.2371354)
        ])


class SuspectChangesetFactory(ChangesetFactory):
    form_create = 2000
    modify = 10
    delete = 30
    is_suspect = True


class HarmfulChangesetFactory(SuspectChangesetFactory):
    checked = True
    check_user = factory.SubFactory(UserFactory)
    check_date = factory.LazyFunction(datetime.now)
    harmful = True


class GoodChangesetFactory(HarmfulChangesetFactory):
    harmful = False


class SuspicionReasonsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SuspicionReasons


class HarmfulReasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HarmfulReason


class UserWhitelistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserWhitelist
