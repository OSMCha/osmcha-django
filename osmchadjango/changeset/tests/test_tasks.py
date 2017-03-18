# -*- coding: utf-8 -*-
from django.test import TestCase

from ..models import Changeset, SuspicionReasons
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

    def test_create_changeset_without_tags(self):
        create_changeset(46755934)
        self.assertEqual(Changeset.objects.count(), 1)
        ch = Changeset.objects.get(id=46755934)
        self.assertIsNone(ch.editor)
        self.assertTrue(ch.is_suspect)
        self.assertTrue(ch.powerfull_editor)
        self.assertEqual(
            SuspicionReasons.objects.filter(
                name='Software editor was not declared'
                ).count(),
            1
            )


class TestGetLastReplicationID(TestCase):
    def test_get_last_replication_id(self):
        sequence = get_last_replication_id()
        self.assertIsNotNone(sequence)
        self.assertIsInstance(sequence, int)
