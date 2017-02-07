import json

from django.test import TestCase
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from django.db.utils import IntegrityError

from ...changeset.tests.modelfactories import ChangesetFactory
from ...changeset.models import SuspicionReasons
from ..models import Feature


class TestFeatureModel(TestCase):
    def setUp(self):
        self.geojson = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-24.json')(),
            'r'
            ))
        self.old_geojson = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-23.json')(),
            'r'
            ))
        self.changeset = ChangesetFactory()
        self.feature = Feature.objects.create(
            changeset=self.changeset,
            osm_id=169218447,
            osm_type='way',
            osm_version=24,
            geometry=GEOSGeometry(json.dumps(self.geojson['geometry'])),
            old_geometry=GEOSGeometry(
                json.dumps(self.geojson['properties']['oldVersion']['geometry'])
                ),
            geojson=self.geojson,
            old_geojson=self.old_geojson,
            url='way-169218447'
            )
        self.reason = SuspicionReasons.objects.create(
            name='new mapper edits'
            )
        self.reason.features.add(self.feature)

    def test_feature_creation(self):
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(
            self.feature.osm_link(),
            'http://www.openstreetmap.org/way/169218447'
            )
        self.assertEqual(self.feature.reasons.count(), 1)
        self.assertEqual(len(self.feature.all_tags), 15)

    def test_forbid_duplicated(self):
        with self.assertRaises(IntegrityError):
            Feature.objects.create(
                changeset=self.changeset,
                osm_id=169218447,
                osm_type='way',
                osm_version=24,
                geometry=GEOSGeometry(json.dumps(self.geojson['geometry'])),
                old_geometry=GEOSGeometry(
                    json.dumps(self.geojson['properties']['oldVersion']['geometry'])
                    ),
                geojson=self.geojson,
                old_geojson=self.old_geojson,
                url='way-169218447'
                )
