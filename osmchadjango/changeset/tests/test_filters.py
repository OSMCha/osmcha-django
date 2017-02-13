from datetime import date, timedelta

from django.test import TestCase

from ..filters import ChangesetFilter
from ..filters import Changeset
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, UserFactory,
    HarmfulChangesetFactory, GoodChangesetFactory,
    )


class TestChangesetFilter(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test_user')
        self.user_2 = UserFactory(username='test_user_2')
        ChangesetFactory(editor='iD 2.0.2', comment='My first edit')
        SuspectChangesetFactory(user='suspect_user', uid='343', source='Bing')
        HarmfulChangesetFactory(check_user=self.user)
        GoodChangesetFactory(check_user=self.user_2, source='Mapbox')

    def test_method_filters(self):
        self.assertEqual(Changeset.objects.count(), 4)
        self.assertEqual(ChangesetFilter({'checked': 'True'}).count(), 2)
        self.assertEqual(ChangesetFilter({'checked': 'False'}).count(), 2)
        self.assertEqual(ChangesetFilter({'is_suspect': 'True'}).count(), 3)
        self.assertEqual(ChangesetFilter({'harmful': 'True'}).count(), 1)
        self.assertEqual(ChangesetFilter({'harmful': 'False'}).count(), 1)
        self.assertEqual(
            ChangesetFilter({'bbox': '-2.143,50.560,2.172,51.986'}).count(), 0
            )
        self.assertEqual(ChangesetFilter({'bbox': '-72,43,-70,45'}).count(), 4)
        self.assertEqual(
            ChangesetFilter({'usernames': 'suspect_user'}).count(), 1)
        self.assertEqual(
            ChangesetFilter({'usernames': 'suspect_user,test'}).count(), 4
            )
        self.assertEqual(
            ChangesetFilter({'checked_by': self.user.username}).count(), 1
            )
        self.assertEqual(
            ChangesetFilter(
                {'checked_by': '{},{}'.format(self.user.username, self.user_2.username)}
                ).count(),
            2
            )

    def test_field_filters(self):
        self.assertEqual(ChangesetFilter({'create__gte': 2000}).count(), 3)
        self.assertEqual(ChangesetFilter({'create__lte': 1000}).count(), 1)
        self.assertEqual(ChangesetFilter({'delete__gte': 30}).count(), 3)
        self.assertEqual(ChangesetFilter({'delete__lte': 10}).count(), 1)
        self.assertEqual(ChangesetFilter({'modify__gte': 30}).count(), 0)
        self.assertEqual(ChangesetFilter({'modify__lte': 10}).count(), 4)
        self.assertEqual(
            ChangesetFilter({'date__gte': date.today()}).count(), 4
            )
        self.assertEqual(
            ChangesetFilter(
                {'date__gte': date.today() + timedelta(days=1)}
                ).count(),
            0
            )
        self.assertEqual(
            ChangesetFilter(
                {'date__lte': date.today() + timedelta(days=1)}
                ).count(),
            4
            )
        self.assertEqual(
            ChangesetFilter(
                {'date__lte': date.today() - timedelta(days=1)}
                ).count(),
            0
            )
        self.assertEqual(ChangesetFilter({'editor__icontains': 'id'}).count(), 1)
        self.assertEqual(ChangesetFilter({'editor': 'Potlatch 2'}).count(), 3)
        self.assertEqual(
            ChangesetFilter({'editor__icontains': 'potlatch'}).count(), 3
            )
        self.assertEqual(
            ChangesetFilter({'comment': 'My first edit'}).count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'comment__icontains': 'edit'}).count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'comment__icontains': 'import'}).count(), 0
            )
        self.assertEqual(ChangesetFilter({'source': 'Mapbox'}).count(), 1)
        self.assertEqual(ChangesetFilter({'source': 'Bing'}).count(), 1)
        self.assertEqual(
            ChangesetFilter({'source__icontains': 'Mapbox'}).count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'source__icontains': 'Google'}).count(), 0
            )
