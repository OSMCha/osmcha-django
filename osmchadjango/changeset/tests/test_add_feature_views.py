import sys
import json
from datetime import datetime
from unittest import mock, skipIf
import requests

from django.test import override_settings
from django.urls import reverse
from django.conf import settings

from social_django.models import UserSocialAuth
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from ...users.models import User
from ...roulette_integration.models import ChallengeIntegration
from ...roulette_integration.utils import format_challenge_task_payload

from ..models import SuspicionReasons, Tag, Changeset
from .modelfactories import ChangesetFactory


class TestAddFeatureToChangesetView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123'
            )

        self.staff_user = User.objects.create_user(
            username='staff_test',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='443324'
            )

        self.data = {
            "osm_id": 877656232,
            "osm_type": "node",
            "version": 54,
            "changeset": 1234,
            "name": "Salvador",
            "primary_tags": {"office": "coworking", "building": "yes"},
            "reasons": ["Deleted place", "Deleted wikidata"]
            }
        self.data_2 = {
            "osm_id": 877656333,
            "osm_type": "node",
            "version": 44,
            "changeset": 1234,
            "reasons": ["Deleted address"],
            "note": "suspect to be a graffiti",
            "uid": 9999,
            "user": "TestUser"
            }
        self.data_3 = {
            "osm_id": 87765444,
            "changeset": 4965,
            "osm_type": "node",
            "version": 44,
            "reasons": ["Deleted Motorway"]
            }
        self.changeset = ChangesetFactory(id=4965)
        self.url = reverse('changeset:add-feature')

    def test_unauthenticated_can_not_add_feature(self):
        """Unauthenticated requests should return a 401 error."""
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Changeset.objects.filter(id=1234).count(), 0)

    def test_non_staff_user_can_not_add_feature(self):
        """Non staff users requests should return a 403 error."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Changeset.objects.filter(id=1234).count(), 0)

    def test_add_feature(self):
        """When adding a feature to a changeset that does not exist in the
        database, it must create the changeset with the basic info contained in
        the feature.
        """
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        reasons = SuspicionReasons.objects.filter(
            name__in=self.data.get('reasons')
            )
        self.assertEqual(
            Changeset.objects.get(id=self.data.get('changeset')).new_features,
            [{
                "osm_id": 877656232,
                "url": "node-877656232",
                "version": 54,
                "name": "Salvador",
                "primary_tags": {"office": "coworking", "building": "yes"},
                "reasons": [i.id for i in reasons]
            }]
        )
        self.assertEqual(
            Changeset.objects.get(id=self.data.get('changeset')).reasons.count(),
            2
            )

        # Add another feature to the same changeset
        response = self.client.post(self.url, data=self.data_2)
        reasons_2 = SuspicionReasons.objects.filter(
            name__in=self.data_2.get('reasons')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(Changeset.objects.get(id=1234).new_features),
            2
            )
        self.assertIn(
            877656232,
            [i.get('osm_id') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            877656333,
            [i.get('osm_id') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            "node-877656232",
            [i.get('url') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            "node-877656333",
            [i.get('url') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            [i.id for i in reasons],
            [i.get('reasons') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            set([i.id for i in reasons_2]),
            [set(i.get('reasons')) for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            "suspect to be a graffiti",
            [i.get('note') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            54,
            [i.get('version') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertIn(
            44,
            [i.get('version') for i in Changeset.objects.get(id=1234).new_features],
            )
        self.assertEqual(Changeset.objects.get(id=1234).reasons.count(), 3)

    def test_add_feature_with_reason_id(self):
        """When creating a changeset, we can inform the id of the reason instead
        of the name.
        """
        self.client.login(username=self.staff_user.username, password='password')
        reason = SuspicionReasons.objects.create(name='Deleted address')
        payload = {
            "osm_id": 877656232,
            "changeset": 1234,
            "osm_type": "node",
            "version": 54,
            "name": "Tall Building",
            "reasons": [reason.id],
            "note": "suspect to be a graffiti"
            }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Changeset.objects.get(id=self.data.get('changeset')).new_features,
            [{
                "osm_id": 877656232,
                "url": "node-877656232",
                "version": 54,
                "name": "Tall Building",
                "reasons": [reason.id],
                "note": "suspect to be a graffiti"
            }]
        )
        self.assertEqual(
            Changeset.objects.get(id=self.data.get('changeset')).reasons.count(),
            1
            )

    def test_add_feature_to_existent_changeset(self):
        """Adding a feature to an existent changeset."""
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.post(self.url, data=self.data_3)
        reasons = SuspicionReasons.objects.filter(
            name__in=self.data_3.get('reasons')
            )
        self.assertEqual(response.status_code, 200)
        self.changeset.refresh_from_db()
        self.assertEqual(
            self.changeset.new_features,
            [{
                "osm_id": 87765444,
                "url": "node-87765444",
                "version": 44,
                "reasons": [i.id for i in reasons]
            }]
            )
        self.assertEqual(
            Changeset.objects.get(id=self.data_3.get('changeset')).reasons.count(),
            1
            )

    def test_add_same_feature_twice(self):
        """If a feature with the same url is added twice, it should add the
        suspicion reason to the existing feature.
        """
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.post(self.url, data=self.data_3)
        self.assertEqual(response.status_code, 200)

        self.data_3['reasons'] = ["Relevant object deleted"]
        response = self.client.post(self.url, data=self.data_3)
        self.assertEqual(response.status_code, 200)
        self.changeset.refresh_from_db()
        self.assertEqual(len(self.changeset.new_features), 1)
        self.assertEqual(self.changeset.new_features[0]['osm_id'], 87765444)
        self.assertIn(
            SuspicionReasons.objects.get(name="Deleted Motorway").id,
            self.changeset.new_features[0]['reasons']
            )
        self.assertIn(
            SuspicionReasons.objects.get(name="Relevant object deleted").id,
            self.changeset.new_features[0]['reasons']
            )
        self.assertEqual(
            Changeset.objects.get(id=self.data_3.get('changeset')).reasons.count(),
            2
            )

    def test_validation(self):
        self.client.login(username=self.staff_user.username, password='password')
        # validate osm_id
        payload = {
            "osm_id": "asdfs",
            "changeset": 1234,
            "osm_type": "node",
            "version": 54,
            "name": "Tall Building",
            "reasons": ["Other reason"],
            }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)
        # validate changeset
        payload = {
            "osm_id": 12312,
            "changeset": "123-32",
            "osm_type": "node",
            "version": 54,
            "name": "Tall Building",
            "reasons": ["Other reason"],
            }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)
        # validate osm_type
        payload = {
            "osm_id": 12312,
            "changeset": 1234,
            "osm_type": "area",
            "version": 54,
            "name": "Tall Building",
            "reasons": ["Other reason"],
            }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)
        # validate reasons
        payload = {
            "osm_id": 12312,
            "changeset": 1234,
            "osm_type": "way",
            "version": 54,
            "name": "Tall Building",
            "reasons": "Other reason",
            }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)
        payload = {
            "osm_id": 12312,
            "changeset": 1234,
            "osm_type": "way",
            "version": 54,
            "name": "Tall Building",
            "reasons": 1,
            }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)


class TestCreateFeatureV1(APITestCase):
    def setUp(self):
        self.fixture = json.load(open(
            settings.APPS_DIR.path('changeset/tests/test_fixtures/way-23.json')(),
            'r'
            ))
        self.new_fixture = json.load(open(
            settings.APPS_DIR.path('changeset/tests/test_fixtures/way-24.json')(),
            'r'
            ))
        self.unvisible_fixture = json.load(open(
            settings.APPS_DIR.path(
                'changeset/tests/test_fixtures/way-23-with-unvisible-reason.json'
                )(),
            'r'
            ))
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com',
            is_staff=True,
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.token = Token.objects.create(user=self.user)

    def test_create_feature(self):
        response = self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(SuspicionReasons.objects.count(), 2)
        self.assertEqual(Changeset.objects.filter(is_suspect=True).count(), 1)
        changeset = Changeset.objects.get(id=42893048)
        self.assertEqual(changeset.reasons.count(), 2)
        feature = changeset.new_features[0]
        self.assertEqual(feature['osm_id'], 169218447)
        self.assertEqual(feature['url'], 'way-169218447')
        self.assertEqual(feature['name'], 'High Street')
        self.assertEqual(feature['version'], 23)
        self.assertEqual(feature['note'], "Vandalism")
        self.assertEqual(feature['primary_tags'], {"highway": "tertiary"})
        self.assertEqual(len(feature.get('reasons')), 2)

    def test_unathenticated_request(self):
        response = self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            )
        self.assertEqual(response.status_code, 401)

    def test_is_not_staff_user_request(self):
        user = User.objects.create_user(
            username='test_2',
            password='password',
            email='b@a.com',
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='444444',
            )
        token = Token.objects.create(user=user)
        response = self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.new_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(token.key)
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Changeset.objects.count(), 0)

    def test_update_changeset(self):
        Changeset.objects.create(
            id=self.fixture['properties'].get('osm:changeset'),
            uid=self.fixture['properties'].get('osm:uid'),
            user=self.fixture['properties'].get('osm:user'),
            date=datetime.utcfromtimestamp(
                self.fixture['properties'].get('osm:timestamp') / 1000
                ),
            is_suspect=False
            )
        response = self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Changeset.objects.count(), 1)
        self.assertEqual(Changeset.objects.filter(is_suspect=True).count(), 1)

    def test_create_feature_two_times_with_different_reasons(self):
        response = self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.unvisible_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)
        changeset = Changeset.objects.get(id=42893048)
        self.assertEqual(len(changeset.new_features), 1)

        self.assertEqual(len(changeset.new_features[0].get('reasons')), 3)
        self.assertEqual(SuspicionReasons.objects.count(), 3)

    @skipIf(
        sys.version_info < (3,6),
        "Python 3.5 has a different dict ordering that makes this test to fail"
        )
    @override_settings(MAP_ROULETTE_API_KEY='xyz')
    @override_settings(MAP_ROULETTE_API_URL='https://maproulette.org/api/v2')
    @mock.patch.object(requests, 'post')
    def test_maproulette_integration(self, mocked_post):
        """Only one Challenge and only one suspicion reason assigned to it,
            so it should trigger only one request.
        """
        reason_1 = SuspicionReasons.objects.create(name="new mapper edits")
        integration_1 = ChallengeIntegration.objects.create(
            challenge_id=1234, user=self.user
            )
        integration_1.reasons.add(reason_1)

        class MockResponse():
            status_code = 200
        mocked_post.return_value = MockResponse

        self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        mocked_post.assert_called_once_with(
            'https://maproulette.org/api/v2/task',
            headers={
                "Content-Type": "application/json",
                "apiKey": "xyz"
                },
            data=format_challenge_task_payload(
                {
                    "type": "Feature",
                    "geometry": self.fixture.get('geometry'),
                    "properties": self.fixture.get('properties')
                },
                1234,
                169218447,
                ["new mapper edits", "moved an object a significant amount"]
                )
        )

    @skipIf(
        sys.version_info < (3,6),
        "Python 3.5 has a different dict ordering that makes this test to fail"
        )
    @override_settings(MAP_ROULETTE_API_KEY='xyz')
    @override_settings(MAP_ROULETTE_API_URL='https://maproulette.org/api/v2')
    @mock.patch.object(requests, 'post')
    def test_maproulette_integration_with_two_reasons(self, mocked_post):
        """Two suspicion reasons assigned to one Challenge,
            so it should trigger only one request.
        """
        reason_1 = SuspicionReasons.objects.create(name="new mapper edits")
        reason_2 = SuspicionReasons.objects.create(
            name="moved an object a significant amount"
            )
        integration_1 = ChallengeIntegration.objects.create(
            challenge_id=1234, user=self.user
            )
        integration_1.reasons.add(reason_1)
        integration_1.reasons.add(reason_2)

        class MockResponse():
            status_code = 200
        mocked_post.return_value = MockResponse

        self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        mocked_post.assert_called_once_with(
            'https://maproulette.org/api/v2/task',
            headers={
                "Content-Type": "application/json",
                "apiKey": "xyz"
                },
            data=format_challenge_task_payload(
                {
                    "type": "Feature",
                    "geometry": self.fixture.get('geometry'),
                    "properties": self.fixture.get('properties')
                },
                1234,
                169218447,
                ["new mapper edits", "moved an object a significant amount"]
                )
        )

    @skipIf(
        sys.version_info < (3,6),
        "Python 3.5 has a different dict ordering that makes this test to fail"
        )
    @override_settings(MAP_ROULETTE_API_KEY='xyz')
    @override_settings(MAP_ROULETTE_API_URL='https://maproulette.org/api/v2')
    @mock.patch.object(requests, 'post')
    def test_maproulette_integration_called_twice(self, mocked_post):
        """If a feature has two suspicion reasons and each of them are assigned
        to different Challenges, it should make two requests to MapRoulette API.
        """
        reason_1 = SuspicionReasons.objects.create(name="new mapper edits")
        reason_2 = SuspicionReasons.objects.create(
            name="moved an object a significant amount"
            )
        integration_1 = ChallengeIntegration.objects.create(
            challenge_id=1234, user=self.user
            )
        integration_1.reasons.add(reason_1)
        integration_2 = ChallengeIntegration.objects.create(
            challenge_id=4321, user=self.user
            )
        integration_2.reasons.add(reason_2)

        class MockResponse():
            status_code = 200
        mocked_post.return_value = MockResponse

        self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        calls = [
            mock.call(
                'https://maproulette.org/api/v2/task',
                headers={
                    "Content-Type": "application/json",
                    "apiKey": "xyz"
                    },
                data=format_challenge_task_payload(
                    {
                        "type": "Feature",
                        "geometry": self.fixture.get('geometry'),
                        "properties": self.fixture.get('properties')
                    },
                    4321,
                    169218447,
                    ["moved an object a significant amount", "new mapper edits"]
                    )
            ),
            mock.call(
                'https://maproulette.org/api/v2/task',
                headers={
                    "Content-Type": "application/json",
                    "apiKey": "xyz"
                    },
                data=format_challenge_task_payload(
                    {
                        "type": "Feature",
                        "geometry": self.fixture.get('geometry'),
                        "properties": self.fixture.get('properties')
                    },
                    1234,
                    169218447,
                    ["moved an object a significant amount", "new mapper edits"]
                    )
            )
        ]
        mocked_post.assert_has_calls(calls, any_order=True )

    @mock.patch.object(requests, 'post')
    def test_maproulette_integration_not_called(self, mocked_post):
        reason = SuspicionReasons.objects.create(name="new mapper edits")
        integration = ChallengeIntegration.objects.create(challenge_id=1234, user=self.user)
        integration.reasons.add(reason)

        class MockResponse():
            status_code = 200
        mocked_post.return_value = MockResponse

        self.client.post(
            reverse('changeset:add-feature-v1'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        mocked_post.assert_not_called()
