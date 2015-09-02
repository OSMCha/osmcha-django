# -*- coding: utf-8 -*-
from django.test import TestCase

from ..models import Changeset
from ..utils import create_changeset, format_url


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
