import json

from django.test import TestCase
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings

from ...changeset.tests.modelfactories import ChangesetFactory
from ...changeset.models import SuspicionReasons
from ..models import Feature


class TestFeatureModel(TestCase):
    def setUp(self):
        self.geojson = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/line.json')(),
            'r'
            ))
        self.feature = Feature.objects.create(
            changeset=ChangesetFactory(),
            osm_id=169218447,
            osm_type='way',
            osm_version=14,
            geometry=GEOSGeometry(json.dumps(self.geojson['geometry'])),
            old_geometry=GEOSGeometry(
                json.dumps(self.geojson['properties']['oldVersion']['geometry'])
                ),
            geojson=self.geojson,
            )
        self.reason = SuspicionReasons.objects.create(
            name='new mapper edits'
            )
        self.reason.features.add(self.feature)
        self.reason_2 = SuspicionReasons.objects.create(
            name='moved an object a significant amount'
            )
        self.reason_2.features.add(self.feature)

    def test_feature_creation(self):
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(
            self.feature.osm_link(),
            'http://www.openstreetmap.org/way/169218447'
            )
        self.assertEqual(self.feature.reasons.count(), 2)
        self.assertEqual(type(self.feature.all_tags), list)
        self.assertGreater(len(self.feature.all_tags), 0)
