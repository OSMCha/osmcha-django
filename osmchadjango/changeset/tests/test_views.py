from datetime import datetime

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Polygon

from ..models import SuspicionReasons, Changeset

client = Client()


class TestChangesetListView(TestCase):

    def setUp(self):
        pass

    def test_changeset_home_response(self):
        response = client.get(reverse('changeset:home'))
        self.assertEqual(response.status_code, 200)


class TestChangesetDetailView(TestCase):

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

    def test_changeset_detail_response(self):
        response = client.get(reverse('changeset:detail', args=[self.changeset.id]))
        self.assertEqual(response.status_code, 200)