import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.conf import settings

from ..models import Feature


class TestFeatureSuspicionCreate(TestCase):
    def setUp(self):
        self.client = Client()
        self.fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-23.json')(),
            'r'
            ))
        self.new_fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-24.json')(),
            'r'
            ))
        settings.FEATURE_CREATION_KEYS = ['secret']

    def test_suspicion_create(self):
        response = self.client.post(
            reverse('feature:create_suspicion') + '?key=secret',
            data=json.dumps(self.fixture),
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('feature:create_suspicion') + '?key=secret',
            data=json.dumps(self.new_fixture),
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Feature.objects.count(), 2)

    def test_duplicate_suspicion_create(self):
        response = self.client.post(
            reverse('feature:create_suspicion') + '?key=secret',
            data=self.fixture,
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 400)

    def test_unathenticated_suspicion_create(self):
        response = self.client.post(
            reverse('feature:create_suspicion'),
            data=self.fixture,
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 401)
