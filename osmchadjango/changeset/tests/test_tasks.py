# -*- coding: utf-8 -*-
from django.test import TestCase

from ..models import Changeset, UserDetail
from ..tasks import create_changeset, format_url, get_last_replication_id


class TestFormatURL(TestCase):

    def test_format_url(self):
        self.assertEqual(
            format_url(1473773),
            'http://planet.openstreetmap.org/replication/changesets/001/473/773.osm.gz'
        )


class TestCreateChangeset(TestCase):

    def test_creation(self):
        create_changeset(31450443)
        self.assertEqual(Changeset.objects.count(), 1)

    def test_user_details(self):
        self.assertEqual(Changeset.objects.count(), 0)
        create_changeset(31450443)
        self.assertEqual(Changeset.objects.count(), 1)

        changeset = Changeset.objects.all()[:1].get()
        self.assertIsNotNone(changeset.user_detail)
        self.assertEqual(changeset.user_detail.contributor_name, 'Tobsen Laufi')

    def test_user_details_with_multiple_changeset_from_save_user(self):
        self.assertEqual(UserDetail.objects.count(), 0)
        create_changeset(37278802)  # Random edit from user bkowshik
        self.assertEqual(UserDetail.objects.count(), 1)
        create_changeset(37278771) # Random edit from user bkowshik
        self.assertEqual(UserDetail.objects.count(), 1)


class TestGetLastReplicationID(TestCase):
    def test_get_last_replication_id(self):
        sequence = get_last_replication_id()
        self.assertIsNotNone(sequence)
        self.assertIsInstance(sequence, int)
