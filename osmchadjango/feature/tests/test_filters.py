from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from ...changeset.tests.modelfactories import (
    SuspicionReasonsFactory, TagFactory
    )
from ..filters import FeatureFilter
from .modelfactories import (
    FeatureFactory, WayFeatureFactory, CheckedFeatureFactory
    )

User = get_user_model()


class TestFeatureFilter(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='the_user_1', email='a@b.com', name='The User')
        self.feature = FeatureFactory()
        self.way_feature = WayFeatureFactory()
        self.checked_feature = CheckedFeatureFactory(check_user=self.user)

    def test_osm_type_filter(self):
        self.assertEqual(FeatureFilter({'osm_type': 'node'}).qs.count(), 2)
        self.assertEqual(FeatureFilter({'osm_type': 'way'}).qs.count(), 1)

    def test_checked_and_is_harmful_filters(self):
        CheckedFeatureFactory(harmful=False)
        self.assertEqual(FeatureFilter({'checked': 'true'}).qs.count(), 2)
        self.assertEqual(FeatureFilter({'checked': 'false'}).qs.count(), 2)
        self.assertEqual(FeatureFilter({'harmful': 'false'}).qs.count(), 1)
        self.assertEqual(FeatureFilter({'harmful': 'true'}).qs.count(), 1)

    def test_char_filters(self):
        self.assertEqual(
            FeatureFilter({'editor': 'JOSM'}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter({'editor': 'Potlatch 2'}).qs.count(), 3
            )

    def test_changeset_ids_filter(self):
        changeset_ids = '{},{}'.format(
            self.feature.changeset.id, self.way_feature.changeset.id
            )
        self.assertEqual(
            FeatureFilter({'changeset_ids': changeset_ids}).qs.count(), 2
            )
        id = self.checked_feature.changeset.id
        self.assertEqual(
            FeatureFilter({'changeset_ids': id}).qs.count(), 1
            )

    def test_date_filters(self):
        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)
        CheckedFeatureFactory(check_date=tomorrow)
        self.assertEqual(
            FeatureFilter({'date__gte': yesterday}).qs.count(), 4
            )
        self.assertEqual(
            FeatureFilter({'date__lte': yesterday}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter({'date__gte': tomorrow}).qs.count(), 0
            )

        next_hour = timezone.now() + timedelta(hours=1)
        self.assertEqual(
            FeatureFilter({'date__gte': next_hour}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter({'date__lte': next_hour}).qs.count(), 4
            )

        self.assertEqual(
            FeatureFilter({'check_date__gte': tomorrow}).qs.count(), 1
            )
        self.assertEqual(
            FeatureFilter({'check_date__gte': yesterday}).qs.count(), 2
            )
        self.assertEqual(
            FeatureFilter({'check_date__lte': yesterday}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter({'check_date__gte': next_hour}).qs.count(), 1
            )
        self.assertEqual(
            FeatureFilter({'check_date__lte': next_hour}).qs.count(), 1
            )

    def test_users_filters(self):
        user_2 = User.objects.create(
            username='the_user_2', email='b@b.com', name="The User 2")
        CheckedFeatureFactory(check_user=user_2)
        # test filter by checked_by
        self.assertEqual(
            FeatureFilter({'checked_by': 'The User'}).qs.count(), 1
            )
        self.assertEqual(
            FeatureFilter({'checked_by': 'The User,The User 2'}).qs.count(),
            2
            )
        self.assertEqual(
            FeatureFilter({'checked_by': 'the_user_3,another'}).qs.count(), 0
            )
        # test filter by users
        self.assertEqual(
            FeatureFilter({'users': 'test, user'}).qs.count(), 4
            )
        self.assertEqual(
            FeatureFilter({'users': 'bad_user, user'}).qs.count(), 0
            )
        # test filter by uid
        self.assertEqual(
            FeatureFilter({'uids': '123123'}).qs.count(), 4
            )
        self.assertEqual(
            FeatureFilter({'uids': '123123, 7873'}).qs.count(), 4
            )
        self.assertEqual(
            FeatureFilter({'uids': '4132'}).qs.count(), 0
            )

    def test_geometry_filter(self):
        geojson_1 = """{'type': 'Polygon', 'coordinates': [
              [[4, 3], [4, 5], [5, 5], [5, 3], [4, 3]]
            ]}"""
        geojson_2 = """{'type': 'Polygon', 'coordinates': [
              [[40, 13], [40, 15], [43, 15], [43, 13], [40, 13]]
            ]}"""
        self.assertEqual(
            FeatureFilter({'geometry': geojson_1}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter({'geometry': geojson_2}).qs.count(), 3
            )

    def test_suspicion_reasons_filter(self):
        reason_1 = SuspicionReasonsFactory(name='Edited wikidata tag')
        reason_1.features.add(self.feature)
        reason_2 = SuspicionReasonsFactory(name='Changed name tag')
        reason_2.features.add(self.checked_feature, self.feature)
        reason_3 = SuspicionReasonsFactory(name='Deleted all tags')
        self.assertEqual(
            FeatureFilter({'reasons': '{}'.format(reason_1.id)}).qs.count(), 1
            )
        self.assertEqual(
            FeatureFilter({'reasons': '{}'.format(reason_2.id)}).qs.count(), 2
            )
        self.assertEqual(
            FeatureFilter(
                {'reasons': '{},{}'.format(reason_1.id, reason_2.id)}
                ).qs.count(),
            2
            )
        self.assertEqual(
            FeatureFilter({'reasons': '{}'.format(reason_3.id)}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter(
                {'all_reasons': '{},{}'.format(reason_1.id, reason_2.id)}
                ).qs.count(),
            1
            )
        self.assertEqual(
            FeatureFilter(
                {'all_reasons': '{},{}'.format(reason_1.id, reason_3.id)}
                ).qs.count(),
            0
            )

    def test_tag_filter(self):
        tag_1 = TagFactory(name='Vandalism')
        tag_1.features.add(self.feature, self.checked_feature)
        tag_2 = TagFactory(name='Illegal import')
        tag_2.features.add(self.feature)
        tag_3 = TagFactory(name='Small error')

        self.assertEqual(
            FeatureFilter({'tags': '{}'.format(tag_1.id)}).qs.count(), 2
            )
        self.assertEqual(
            FeatureFilter(
                {'tags': '{},{}'.format(tag_1.id, tag_2.id)}
                ).qs.count(),
            2
            )
        self.assertEqual(
            FeatureFilter({'tags': '{}'.format(tag_3.id)}).qs.count(), 0
            )
        self.assertEqual(
            FeatureFilter({'all_tags': '{}'.format(tag_1.id)}).qs.count(), 2
            )
        self.assertEqual(
            FeatureFilter(
                {'all_tags': '{},{}'.format(tag_1.id, tag_2.id)}
                ).qs.count(),
            1
            )
        self.assertEqual(
            FeatureFilter(
                {'all_tags': '{},{}'.format(tag_1.id, tag_3.id)}
                ).qs.count(),
            0
            )
