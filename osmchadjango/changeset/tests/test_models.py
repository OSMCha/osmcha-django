from datetime import datetime

from django.test import TestCase
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError

from ..models import Changeset, SuspicionReasons, Import


class TestChangesetModel(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = Changeset.objects.create(
            id=31982803,
            uid='123123',
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
        self.assertEqual(
            self.changeset.achavi_link(),
            'https://overpass-api.de/achavi/?changeset=31982803'
            )
        self.assertEqual(
            self.changeset.osm_link(),
            'http://www.openstreetmap.org/changeset/31982803'
            )
        self.assertEqual(SuspicionReasons.objects.all().count(), 2)


class TestImportModel(TestCase):
    def setUp(self):
        self.import_1 = Import.objects.create(start=1, end=1000)
        self.import_2 = Import.objects.create(start=1001, end=2000)

    def test_import_creation(self):
        self.assertIsInstance(self.import_1, Import)
        self.assertIsInstance(self.import_1.date, datetime)
        self.assertEqual(self.import_1.__str__(), 'Import 1 - 1000')
        self.assertEqual(Import.objects.count(), 2)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            Import.objects.create(end=1000)

        with self.assertRaises(ValidationError):
            Import.objects.create(start=1000)
