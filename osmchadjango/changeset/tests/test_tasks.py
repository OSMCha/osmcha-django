# -*- coding: utf-8 -*-
from django.test import TestCase

from ..models import Changeset
from ..tasks import create_changeset, format_url, get_last_replication_id


class TestFormatURL(TestCase):

    def test_format_url(self):
        self.assertEqual(
            format_url(1473773),
            'http://planet.openstreetmap.org/replication/changesets/001/473/773.osm.gz'
            )


class TestCreateChangeset(TestCase):

    def test_creation(self):
        changeset = create_changeset(31450443)
        self.assertEqual(Changeset.objects.count(), 1)
        self.assertEqual(
            changeset.bbox.wkt,
            'POLYGON ((-34.9230192 -8.219786900000001, -34.855581 -8.219786900000001, -34.855581 -8.0335263, -34.9230192 -8.0335263, -34.9230192 -8.219786900000001))'
            )


class TestGetLastReplicationID(TestCase):

    def test_get_last_replication_id(self):
        sequence = get_last_replication_id()
        self.assertIsNotNone(sequence)
        self.assertIsInstance(sequence, int)


class TestCreateChangesetWithoutBBOX(TestCase):

    def test_creation(self):
        changeset = create_changeset(47052680)
        self.assertEqual(Changeset.objects.count(), 1)
        self.assertIsNone(changeset.bbox)
