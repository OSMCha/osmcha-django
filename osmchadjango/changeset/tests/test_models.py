from osmcha.changeset import Analyse

from datetime import datetime

from django.test import TestCase
from django.contrib.gis.geos import Polygon, GEOSGeometry

from ..models import Changeset, SuspicionReasons
from ..utils import create_changeset

class TestChangesetCreation(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = Changeset.objects.create(
            id=31982803,
            user='test',
            editor='Potlatch 2',
            powerfull_editor=False,
            date=datetime.now(),
            create=2000,
            modify=10,
            delete=30,
            is_suspect=True,
            bbox=Polygon([
                (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
                (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
                (-71.0646843, 44.2371354)
            ])
        )
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)

    def test_changeset_creation(self):
        self.assertIsInstance(self.changeset, Changeset)
        self.assertEqual(Changeset.objects.all().count(), 1)
        self.assertEqual(self.changeset.reasons.all().count(), 2)
        self.assertFalse(self.changeset.checked)
        self.assertEqual(self.changeset.achavi_link(),
            'https://nrenner.github.io/achavi/?changeset=31982803')
        self.assertEqual(self.changeset.osm_link(),
            'http://www.openstreetmap.org/changeset/31982803')
        self.assertEqual(SuspicionReasons.objects.all().count(), 2)


class TestCreationFromAPI(TestCase):

    def test_creation(self):
        create_changeset(31450443)
        self.assertEqual(Changeset.objects.count(), 1)