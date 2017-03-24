import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework.test import APIClient

from ..models import Feature
from .modelfactories import (
    FeatureFactory, CheckedFeatureFactory, WayFeatureFactory
    )

client = APIClient()


class TestFeatureSuspicionCreate(TestCase):
    def setUp(self):
        client = Client()
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
        response = client.post(
            reverse('feature:create_suspicion') + '?key=secret',
            data=json.dumps(self.fixture),
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 200)

        response = client.post(
            reverse('feature:create_suspicion') + '?key=secret',
            data=json.dumps(self.new_fixture),
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Feature.objects.count(), 2)

    def test_duplicate_suspicion_create(self):
        response = client.post(
            reverse('feature:create_suspicion') + '?key=secret',
            data=self.fixture,
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 400)

    def test_unathenticated_suspicion_create(self):
        response = client.post(
            reverse('feature:create_suspicion'),
            data=self.fixture,
            content_type="application/json"
            )
        self.assertEqual(response.status_code, 401)


class TestFeatureListAPIView(TestCase):
    def setUp(self):
        FeatureFactory.create_batch(15)
        WayFeatureFactory.create_batch(15)
        CheckedFeatureFactory.create_batch(15)
        CheckedFeatureFactory.create_batch(15, harmful=False)
        self.url = reverse('feature:list')

    def test_list_view(self):
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 50)
        self.assertEqual(response.data.get('count'), 60)

    def test_pagination(self):
        response = client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 10)
        self.assertEqual(response.data['count'], 60)
        # test page_size parameter
        response = client.get(self.url, {'page_size': 60})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 60)

    def test_filters(self):
        response = client.get(self.url, {'in_bbox': '40,13,43,15'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 60)
        response = client.get(
            self.url,
            {'in_bbox': '40,13,43,15', 'checked': 'true'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 30)

        response = client.get(self.url, {'in_bbox': '-3.17,-91.98,-2.1,-90.5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = client.get(self.url, {'harmful': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 15)

        response = client.get(self.url, {'harmful': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 15)

    def test_ordering(self):
        # default ordering is by descending changeset id
        response = client.get(self.url)
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.all()[:50]]
            )
