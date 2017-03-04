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
        ChangesetFactory(id=2343, editor='iD 2.0.2', comment='My first edit')
        SuspectChangesetFactory(user='suspect_user', uid='343', source='Bing')
        HarmfulChangesetFactory(
            check_user=self.user,
            editor='JOSM 1.5',
            powerfull_editor=True
            )
        GoodChangesetFactory(check_user=self.user_2, source='Mapbox')

    def test_boolean_filters(self):
        self.assertEqual(Changeset.objects.count(), 4)
        self.assertEqual(ChangesetFilter({'checked': 'True'}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'checked': 'true'}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'checked': True}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'checked': 'False'}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'is_suspect': 'True'}).qs.count(), 3)
        self.assertEqual(ChangesetFilter({'harmful': 'True'}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'harmful': 'False'}).qs.count(), 1)
        self.assertEqual(
            ChangesetFilter({'powerfull_editor': 'True'}).qs.count(), 1
            )

    def test_geo_filters(self):
        geojson_1 = """{'type': 'Polygon', 'coordinates': [
              [[-2.143, 50.56], [-2.143, 51.986], [2.172, 51.986],
              [2.172, 50.56], [-2.143, 50.56]]
            ]}"""
        self.assertEqual(
            ChangesetFilter({'bbox_overlaps': geojson_1}).qs.count(), 0
            )
        geojson_2 = """{'type': 'Polygon','coordinates': [
            [[-71.06,44.237], [-71.004,44.237], [-71.004,44.243],
            [-71.06,44.243],[-71.06,44.237]]
            ]}"""
        self.assertEqual(
            ChangesetFilter({'bbox_overlaps': geojson_2}).qs.count(), 4
            )

    def test_users_related_filters(self):
        self.assertEqual(
            ChangesetFilter({'users': 'suspect_user'}).qs.count(), 1)
        self.assertEqual(
            ChangesetFilter({'users': 'suspect_user,test'}).qs.count(), 4
            )
        self.assertEqual(
            ChangesetFilter({'checked_by': self.user.username}).qs.count(), 1
            )
        users = '{},{}'.format(self.user.username, self.user_2.username)
        self.assertEqual(ChangesetFilter({'checked_by': users}).qs.count(), 2)

    def test_id_filters(self):
        self.assertEqual(ChangesetFilter({'ids': '2343,2344'}).qs.count(), 1)

    def test_number_field_filters(self):
        self.assertEqual(ChangesetFilter({'create__gte': 2000}).qs.count(), 3)
        self.assertEqual(ChangesetFilter({'create__lte': 1000}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'delete__gte': 30}).qs.count(), 3)
        self.assertEqual(ChangesetFilter({'delete__lte': 10}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'modify__gte': 30}).qs.count(), 0)
        self.assertEqual(ChangesetFilter({'modify__lte': 10}).qs.count(), 4)

    def test_date_field_filter(self):
        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)

        self.assertEqual(
            ChangesetFilter({'date__gte': date.today()}).qs.count(), 4
            )
        self.assertEqual(ChangesetFilter({'date__gte': tomorrow}).qs.count(), 0)
        self.assertEqual(ChangesetFilter({'date__lte': tomorrow}).qs.count(), 4)
        self.assertEqual(ChangesetFilter({'date__lte': yesterday}).qs.count(), 0)

    def test_check_date_field_filter(self):
        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)

        self.assertEqual(
            ChangesetFilter({'check_date__lte': yesterday}).qs.count(), 0
            )
        self.assertEqual(
            ChangesetFilter({'check_date__gte': date.today()}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'check_date__lte': tomorrow}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'check_date__gte': tomorrow}).qs.count(), 0
            )

    def test_char_field_filters(self):
        self.assertEqual(
            ChangesetFilter({'editor__icontains': 'id'}).qs.count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'editor': 'Potlatch 2'}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'editor__icontains': 'potlatch'}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'comment': 'My first edit'}).qs.count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'comment__icontains': 'edit'}).qs.count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'comment__icontains': 'import'}).qs.count(), 0
            )
        self.assertEqual(ChangesetFilter({'source': 'Mapbox'}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'source': 'Bing'}).qs.count(), 1)
        self.assertEqual(
            ChangesetFilter({'source__icontains': 'Mapbox'}).qs.count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'source__icontains': 'Google'}).qs.count(), 0
            )
