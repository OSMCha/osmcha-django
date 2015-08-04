from datetime import datetime

from django.test import TestCase
from django.contrib.gis.geos import Polygon

from ..models import Changeset, SuspicionReasons


class TestChangesetCreation(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = Changeset.objects.create(
            id=31982803,
            user='test',
            editor='Potlatch 2',
            date=datetime.now(),
            created=2000,
            modified=10,
            deleted=30,
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
        self.assertEqual(SuspicionReasons.objects.all().count(), 2)

