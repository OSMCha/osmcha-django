import json
from datetime import date

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from social_django.models import UserSocialAuth

from ...changeset.models import (HarmfulReason, SuspicionReasons, Changeset)
from ...users.models import User
from ..models import Feature
from .modelfactories import (
    FeatureFactory, CheckedFeatureFactory, WayFeatureFactory
    )

client = APIClient()


class TestFeatureSuspicionCreate(TestCase):
    def setUp(self):
        self.fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-23.json')(),
            'r'
            ))
        self.new_fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-24.json')(),
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
        response = client.post(
            reverse('feature:create'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)

        response = client.post(
            reverse('feature:create'),
            data=json.dumps(self.new_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Feature.objects.count(), 2)
        self.assertEqual(SuspicionReasons.objects.count(), 2)
        self.assertEqual(Changeset.objects.filter(is_suspect=True).count(), 2)
        feature = Feature.objects.get(
            osm_id=169218447, changeset__id=42893048
            )
        self.assertEqual(feature.url, 'way-169218447')
        self.assertEqual(feature.reasons.count(), 2)
        self.assertTrue(
            feature.geometry.equals(
                GEOSGeometry(json.dumps(self.fixture.get('geometry')))
                )
            )
        self.assertTrue(
            feature.old_geometry.equals(
                GEOSGeometry(
                    json.dumps(self.fixture['properties']['oldVersion'].get('geometry'))
                    )
                )
            )
        self.assertIn('properties', feature.old_geojson.keys())
        self.assertIn('geometry', feature.old_geojson.keys())
        self.assertIn('properties', feature.geojson.keys())
        self.assertIn('geometry', feature.geojson.keys())

    def test_unathenticated_request(self):
        response = client.post(
            reverse('feature:create'),
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
        response = client.post(
            reverse('feature:create'),
            data=json.dumps(self.new_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(token.key)
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Feature.objects.count(), 0)


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


class TestOrderingOfFeatureListAPIView(TestCase):
    def setUp(self):
        CheckedFeatureFactory.create_batch(10)
        self.url = reverse('feature:list')

    def test_ordering(self):
        # default ordering is by descending changeset id
        response = client.get(self.url)
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.all()]
            )
        # ascending changeset id
        response = client.get(self.url, {'order_by': 'changeset_id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('changeset_id')]
            )
        # descending changeset date
        response = client.get(self.url, {'order_by': '-changeset__date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-changeset__date')]
            )
        # ascending changeset date
        response = client.get(self.url, {'order_by': 'changeset__date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('changeset__date')]
            )
        # ascending id
        response = client.get(self.url, {'order_by': 'id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('id')]
            )
        # descending id
        response = client.get(self.url, {'order_by': '-id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-id')]
            )
        # ascending osm_id
        response = client.get(self.url, {'order_by': 'osm_id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('osm_id')]
            )
        # descending osm_id
        response = client.get(self.url, {'order_by': '-osm_id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-osm_id')]
            )
        # ascending check_date
        response = client.get(self.url, {'order_by': 'check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('check_date')]
            )
        # descending check_date
        response = client.get(self.url, {'order_by': '-check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-check_date')]
            )


class TestFeatureDetailAPIView(TestCase):
    def setUp(self):
        self.feature = CheckedFeatureFactory()
        harmful_reason = HarmfulReason.objects.create(name='Vandalism')
        harmful_reason.features.add(self.feature)
        self.reason = SuspicionReasons.objects.create(
            name='new mapper edits'
            )
        self.reason.features.add(self.feature)

    def test_feature_detail_view(self):
        response = client.get(
            reverse(
                'feature:detail',
                args=[self.feature.changeset.id, self.feature.url]
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), self.feature.id)
        self.assertEqual(
            response.data['properties']['osm_id'],
            self.feature.osm_id
            )
        self.assertEqual(
            response.data['properties']['osm_link'],
            self.feature.osm_link()
            )
        self.assertIsInstance(
            response.data['properties']['date'],
            date
            )
        self.assertEqual(
            response.data['properties']['source'],
            self.feature.changeset.source
            )
        self.assertEqual(
            response.data['properties']['comment'],
            self.feature.changeset.comment
            )
        self.assertEqual(
            response.data['properties']['imagery_used'],
            self.feature.changeset.imagery_used
            )
        self.assertEqual(
            response.data['properties']['editor'],
            self.feature.changeset.editor
            )
        self.assertEqual(
            response.data['properties']['url'],
            self.feature.url
            )
        self.assertEqual(
            response.data['properties']['checked'],
            self.feature.checked
            )
        self.assertEqual(
            response.data['properties']['harmful'],
            self.feature.harmful
            )
        self.assertEqual(
            response.data['properties']['check_user'],
            self.feature.check_user.username
            )
        self.assertEqual(
            response.data['properties']['changeset'],
            self.feature.changeset.id
            )
        self.assertIn('properties', response.data.keys())
        self.assertIn('geojson', response.data['properties'].keys())
        self.assertIn('check_date', response.data['properties'].keys())
        self.assertIn('old_geojson', response.data['properties'].keys())
        self.assertIn('geometry', response.data.keys())
        self.assertIn(
            {'name': 'new mapper edits', 'is_visible': True},
            response.data['properties']['reasons']
            )
        self.assertIn(
            {'name': 'Vandalism', 'is_visible': True},
            response.data['properties']['harmful_reasons']
            )
