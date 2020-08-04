import json
import sys
from unittest import mock, skipIf
import requests

from django.test import TestCase, override_settings
from django.conf import settings

from ..utils import (
    format_challenge_task_payload,
    push_feature_to_maproulette,
    remove_unneeded_properties
    )
from ...changeset.tests.modelfactories import SuspicionReasonsFactory

class TestFormatChallengePayload(TestCase):
    def setUp(self):
        self.feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [-110.9595328, 32.2263734]
                },
            'properties': {
                'highway': 'traffic_signals',
                'crossing': 'marked',
                'traffic_signals': 'signal',
                'osm:id': 1234
                },
            }
        self.task_payload = {
            "parent": 1234,
            "name": "987",
            "geometries": {"features": [
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [-110.9595328, 32.2263734]
                        },
                    'properties': {
                        'highway': 'traffic_signals',
                        'crossing': 'marked',
                        'traffic_signals': 'signal',
                        'osmcha_reasons': 'New Mapper, Vandalism'
                        },
                    }
                ]}
            }

    @skipIf(
        sys.version_info < (3,6),
        "Python 3.5 has a different dict ordering that makes this test to fail"
        )
    def test_format_challenge_task_payload(self):
        self.assertEqual(
            format_challenge_task_payload(
                self.feature, 1234, 987, ['New Mapper', 'Vandalism']
                ),
            json.dumps(self.task_payload)
            )

    @override_settings(MAP_ROULETTE_API_KEY='xyz')
    @override_settings(MAP_ROULETTE_API_URL='https://maproulette.org/api/v2')
    @mock.patch.object(requests, 'post')
    def test_push_feature_to_maproulette(self, mocked_post):
        class MockResponse():
            status_code = 200
        mocked_post.return_value = MockResponse

        push_feature_to_maproulette(self.feature, 1234, 987)
        mocked_post.assert_called_with(
            'https://maproulette.org/api/v2/task',
            headers={
                "Content-Type": "application/json",
                "apiKey": "xyz"
                },
            data=format_challenge_task_payload(self.feature, 1234, 987)
        )


class TestRemoveUnneededProperties(TestCase):
    def test_properties_are_removed(self):
        self.fixture = json.load(open(
            settings.APPS_DIR.path('changeset/tests/test_fixtures/way-23.json')(),
            'r'
            ))
        fixture_keys = remove_unneeded_properties(self.fixture)['properties'].keys()
        self.assertNotIn('result:new_mapper', fixture_keys)
        self.assertNotIn('osm:id', fixture_keys)
        self.assertNotIn('osm:changeset', fixture_keys)
        self.assertNotIn('oldVersion', fixture_keys)
