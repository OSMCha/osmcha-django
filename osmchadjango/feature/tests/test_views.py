import json
from datetime import date, datetime

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.test.client import encode_multipart

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from social_django.models import UserSocialAuth

from ...changeset.models import (Tag, SuspicionReasons, Changeset)
from ...changeset.views import PaginatedCSVRenderer
from ...users.models import User
from ..models import Feature
from ..views import FeatureListAPIView
from .modelfactories import (
    FeatureFactory, CheckedFeatureFactory, WayFeatureFactory
    )


class TestCreateFeature(APITestCase):
    def setUp(self):
        self.fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-23.json')(),
            'r'
            ))
        self.new_fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-24.json')(),
            'r'
            ))
        self.unvisible_fixture = json.load(open(
            settings.APPS_DIR.path('feature/tests/fixtures/way-23-with-unvisible-reason.json')(),
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
            reverse('feature:create'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
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
        self.assertNotIn('suspicions', feature.geojson['properties'].keys())
        self.assertIn('geometry', feature.geojson.keys())

    def test_unathenticated_request(self):
        response = self.client.post(
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
        response = self.client.post(
            reverse('feature:create'),
            data=json.dumps(self.new_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(token.key)
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Feature.objects.count(), 0)

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
            reverse('feature:create'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Changeset.objects.count(), 1)
        self.assertEqual(Changeset.objects.filter(is_suspect=True).count(), 1)

    def test_invalid_geometry(self):
        self.fixture['geometry'] = {}
        response = self.client.post(
            reverse('feature:create'),
            data=json.dumps(self.fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Feature.objects.count(), 0)
        self.assertEqual(Changeset.objects.count(), 0)
        self.assertEqual(SuspicionReasons.objects.count(), 0)

    def test_create_feature_with_is_visible_false(self):
        response = self.client.post(
            reverse('feature:create'),
            data=json.dumps(self.unvisible_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(SuspicionReasons.objects.count(), 1)
        self.assertEqual(
            SuspicionReasons.objects.filter(is_visible=False).count(), 1
            )
        self.assertEqual(Changeset.objects.filter(is_suspect=True).count(), 0)

    def test_create_feature_with_is_visible_false_and_suspect_changeset(self):
        Changeset.objects.create(
            id=self.unvisible_fixture['properties'].get('osm:changeset'),
            uid=self.unvisible_fixture['properties'].get('osm:uid'),
            user=self.unvisible_fixture['properties'].get('osm:user'),
            date=datetime.utcfromtimestamp(
                self.unvisible_fixture['properties'].get('osm:timestamp') / 1000
                ),
            is_suspect=True
            )
        response = self.client.post(
            reverse('feature:create'),
            data=json.dumps(self.unvisible_fixture),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(SuspicionReasons.objects.count(), 1)
        self.assertEqual(
            SuspicionReasons.objects.filter(is_visible=False).count(), 1
            )
        self.assertEqual(Changeset.objects.filter(is_suspect=True).count(), 1)


class TestFeatureListAPIView(APITestCase):
    def setUp(self):
        FeatureFactory.create_batch(15)
        WayFeatureFactory.create_batch(15)
        CheckedFeatureFactory.create_batch(15)
        CheckedFeatureFactory.create_batch(15, harmful=False)
        self.url = reverse('feature:list')

    def test_list_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 50)
        self.assertEqual(response.data.get('count'), 60)

    def test_pagination(self):
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 10)
        self.assertEqual(response.data['count'], 60)
        # test page_size parameter
        response = self.client.get(self.url, {'page_size': 60})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 60)

    def test_filters(self):
        response = self.client.get(self.url, {'in_bbox': '40,13,43,15'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 60)
        response = self.client.get(
            self.url,
            {'in_bbox': '40,13,43,15', 'checked': 'true'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 30)

        response = self.client.get(self.url, {'in_bbox': '-3.17,-91.98,-2.1,-90.5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.url, {'harmful': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 15)

        response = self.client.get(self.url, {'harmful': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 15)

    def test_csv_renderer(self):
        self.assertIn(PaginatedCSVRenderer, FeatureListAPIView().renderer_classes)
        response = self.client.get(self.url, {'format': 'csv', 'page_size': 70})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 60)
        response = self.client.get(self.url, {'format': 'csv', 'checked': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 30)


class TestOrderingOfFeatureListAPIView(APITestCase):
    def setUp(self):
        CheckedFeatureFactory.create_batch(10)
        self.url = reverse('feature:list')

    def test_ordering(self):
        # default ordering is by descending changeset id
        response = self.client.get(self.url)
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.all()]
            )
        # ascending changeset id
        response = self.client.get(self.url, {'order_by': 'changeset_id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('changeset_id')]
            )
        # descending changeset date
        response = self.client.get(self.url, {'order_by': '-changeset__date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-changeset__date')]
            )
        # ascending changeset date
        response = self.client.get(self.url, {'order_by': 'changeset__date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('changeset__date')]
            )
        # ascending id
        response = self.client.get(self.url, {'order_by': 'id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('id')]
            )
        # descending id
        response = self.client.get(self.url, {'order_by': '-id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-id')]
            )
        # ascending osm_id
        response = self.client.get(self.url, {'order_by': 'osm_id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('osm_id')]
            )
        # descending osm_id
        response = self.client.get(self.url, {'order_by': '-osm_id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-osm_id')]
            )
        # ascending check_date
        response = self.client.get(self.url, {'order_by': 'check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('check_date')]
            )
        # descending check_date
        response = self.client.get(self.url, {'order_by': '-check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Feature.objects.order_by('-check_date')]
            )


class TestFeatureDetailAPIView(APITestCase):
    def setUp(self):
        self.feature = CheckedFeatureFactory()

    def test_feature_detail_view(self):
        response = self.client.get(
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


class TestReasonsAndTagsFields(APITestCase):
    def setUp(self):
        self.feature = CheckedFeatureFactory()
        tag = Tag.objects.create(name='Vandalism')
        tag.features.add(self.feature)
        private_tag = Tag.objects.create(
            name='Bad feature in my city',
            is_visible=False
            )
        private_tag.features.add(self.feature)
        self.reason = SuspicionReasons.objects.create(
            name='new mapper edits'
            )
        self.reason.features.add(self.feature)
        private_reason = SuspicionReasons.objects.create(
            name='Suspicious Feature in my city',
            is_visible=False
            )
        private_reason.features.add(self.feature)
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )

    def test_detail_view_with_normal_user(self):
        response = self.client.get(
            reverse(
                'feature:detail',
                args=[self.feature.changeset.id, self.feature.url]
                )
            )
        self.assertIn(
            'new mapper edits',
            response.data['properties']['reasons']
            )
        self.assertIn(
            'Vandalism',
            response.data['properties']['tags']
            )
        self.assertNotIn(
            'Suspicious Feature in my city',
            response.data['properties']['reasons']
            )
        self.assertNotIn(
            'Bad feature in my city',
            response.data['properties']['tags']
            )

    def test_list_view_with_normal_user(self):
        response = self.client.get(reverse('feature:list'))
        self.assertIn(
            'new mapper edits',
            response.data['features'][0]['properties']['reasons']
            )
        self.assertIn(
            'Vandalism',
            response.data['features'][0]['properties']['tags']
            )
        self.assertNotIn(
            'Suspicious Feature in my city',
            response.data['features'][0]['properties']['reasons']
            )
        self.assertNotIn(
            'Bad feature in my city',
            response.data['features'][0]['properties']['tags']
            )

    def test_detail_view_with_admin(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse(
                'feature:detail',
                args=[self.feature.changeset.id, self.feature.url]
                )
            )
        self.assertIn(
            'Suspicious Feature in my city',
            response.data['properties']['reasons']
            )
        self.assertIn(
            'new mapper edits',
            response.data['properties']['reasons']
            )
        self.assertIn(
            'Bad feature in my city',
            response.data['properties']['tags']
            )
        self.assertIn(
            'Vandalism',
            response.data['properties']['tags']
            )

    def test_list_view_with_admin(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('feature:list'))
        self.assertIn(
            'Suspicious Feature in my city',
            response.data['features'][0]['properties']['reasons']
            )
        self.assertIn(
            'new mapper edits',
            response.data['features'][0]['properties']['reasons']
            )
        self.assertIn(
            'Bad feature in my city',
            response.data['features'][0]['properties']['tags']
            )
        self.assertIn(
            'Vandalism',
            response.data['features'][0]['properties']['tags']
            )


class TestCheckFeatureViews(APITestCase):
    def setUp(self):
        self.feature = FeatureFactory()
        self.user = User.objects.create_user(
            username='test_user',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='44444',
            )
        self.changeset_user = User.objects.create_user(
            username='test',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.changeset_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.tag_1 = Tag.objects.create(name='Illegal import')
        self.tag_2 = Tag.objects.create(name='Vandalism')
        self.set_harmful_url = reverse(
            'feature:set-harmful',
            args=[self.feature.changeset, self.feature.url]
            )
        self.set_good_url = reverse(
            'feature:set-good',
            args=[self.feature.changeset.id, self.feature.url]
            )

    def test_check_feature_unauthenticated(self):
        response = self.client.put(self.set_harmful_url)
        self.assertEqual(response.status_code, 401)
        self.feature.refresh_from_db()
        self.assertIsNone(self.feature.harmful)
        self.assertFalse(self.feature.checked)

        response = self.client.put(self.set_good_url)
        self.assertEqual(response.status_code, 401)
        self.feature.refresh_from_db()
        self.assertIsNone(self.feature.harmful)
        self.assertFalse(self.feature.checked)

    def test_set_harmful_feature_not_allowed(self):
        """User can't mark the feature as harmful because he is the author of
        the changeset that modified the feature.
        """
        self.client.login(username=self.changeset_user.username, password='password')
        response = self.client.put(self.set_harmful_url)
        self.assertEqual(response.status_code, 403)
        self.feature.refresh_from_db()
        self.assertIsNone(self.feature.harmful)
        self.assertFalse(self.feature.checked)
        self.assertIsNone(self.feature.check_user)
        self.assertIsNone(self.feature.check_date)

    def test_set_good_feature_not_allowed(self):
        """User can't mark the feature as good because he is the author of
        the changeset that modified the feature.
        """
        self.client.login(username=self.changeset_user.username, password='password')
        response = self.client.put(self.set_good_url)
        self.assertEqual(response.status_code, 403)
        self.feature.refresh_from_db()
        self.assertIsNone(self.feature.harmful)
        self.assertFalse(self.feature.checked)
        self.assertIsNone(self.feature.check_user)
        self.assertIsNone(self.feature.check_date)

    def test_set_harmful_feature_with_tags(self):
        self.client.login(username=self.user.username, password='password')
        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'tags': [self.tag_1.id, self.tag_2.id]}
            )
        response = self.client.put(
            self.set_harmful_url,
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
            )
        self.assertEqual(response.status_code, 200)
        self.feature.refresh_from_db()
        self.assertTrue(self.feature.harmful)
        self.assertTrue(self.feature.checked)
        self.assertEqual(self.feature.tags.count(), 2)
        self.assertIn(self.tag_1, self.feature.tags.all())
        self.assertIn(self.tag_2, self.feature.tags.all())

    def test_set_harmful_feature(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(self.set_harmful_url)
        self.assertEqual(response.status_code, 200)
        self.feature.refresh_from_db()
        self.assertTrue(self.feature.harmful)
        self.assertTrue(self.feature.checked)

    def test_set_good_feature(self):
        self.client.login(username=self.user.username, password='password')
        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'tags': [self.tag_1.id, self.tag_2.id]}
            )
        response = self.client.put(
            self.set_good_url,
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
            )
        self.assertEqual(response.status_code, 200)
        self.feature.refresh_from_db()
        self.assertFalse(self.feature.harmful)
        self.assertTrue(self.feature.checked)
        self.assertEqual(self.feature.tags.count(), 2)
        self.assertIn(self.tag_1, self.feature.tags.all())
        self.assertIn(self.tag_2, self.feature.tags.all())

    def test_set_good_feature_without_tags(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(self.set_good_url)
        self.assertEqual(response.status_code, 200)
        self.feature.refresh_from_db()
        self.assertFalse(self.feature.harmful)
        self.assertTrue(self.feature.checked)

    def test_try_to_check_feature_already_checked(self):
        feature = CheckedFeatureFactory()
        self.client.login(username=self.user.username, password='password')
        # first try to mark a checked feature as good
        response = self.client.put(
            reverse('feature:set-good', args=[feature.changeset, feature.url])
            )
        self.assertEqual(response.status_code, 403)
        feature.refresh_from_db()
        self.assertNotEqual(feature.check_user, self.user)

        # now try to mark a checked feature as harmful
        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'tags': [self.tag_1.id, self.tag_2.id]}
            )
        response = self.client.put(
            reverse('feature:set-harmful', args=[feature.changeset, feature.url]),
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
            )
        self.assertEqual(response.status_code, 403)
        feature.refresh_from_db()
        self.assertNotEqual(feature.check_user, self.user)

    def test_404(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('feature:set-good', args=[4988787832, 'way-16183212']),
            )
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            reverse('feature:set-harmful', args=[4988787832, 'way-16183212']),
            )
        self.assertEqual(response.status_code, 404)


class TestUncheckFeatureView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.feature = FeatureFactory()
        self.good_feature = CheckedFeatureFactory(
            check_user=self.user, harmful=False
            )
        self.harmful_feature = CheckedFeatureFactory(check_user=self.user)
        self.harmful_feature_2 = CheckedFeatureFactory()
        self.tag = Tag.objects.create(name='Vandalism')
        self.tag.features.set(
            [self.harmful_feature, self.harmful_feature_2, self.good_feature]
            )

    def test_unauthenticated_response(self):
        response = self.client.put(
            reverse(
                'feature:uncheck',
                args=[self.harmful_feature.changeset, self.harmful_feature.url]
                )
            )
        self.assertEqual(response.status_code, 401)
        self.harmful_feature.refresh_from_db()
        self.assertTrue(self.harmful_feature.harmful)
        self.assertTrue(self.harmful_feature.checked)
        self.assertEqual(self.harmful_feature.check_user, self.user)
        self.assertIsNotNone(self.harmful_feature.check_date)
        self.assertEqual(self.harmful_feature.tags.count(), 1)
        self.assertIn(self.tag, self.harmful_feature.tags.all())

    def test_uncheck_harmful_feature(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse(
                'feature:uncheck',
                args=[self.harmful_feature.changeset, self.harmful_feature.url]
                )
            )
        self.assertEqual(response.status_code, 200)
        self.harmful_feature.refresh_from_db()
        self.assertIsNone(self.harmful_feature.harmful)
        self.assertFalse(self.harmful_feature.checked)
        self.assertIsNone(self.harmful_feature.check_user)
        self.assertIsNone(self.harmful_feature.check_date)
        self.assertEqual(self.harmful_feature.tags.count(), 0)
        self.assertNotIn(self.harmful_feature, self.tag.changesets.all())

    def test_uncheck_good_feature(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse(
                'feature:uncheck',
                args=[self.good_feature.changeset, self.good_feature.url]
                )
            )
        self.assertEqual(response.status_code, 200)
        self.good_feature.refresh_from_db()
        self.assertIsNone(self.good_feature.harmful)
        self.assertFalse(self.good_feature.checked)
        self.assertIsNone(self.good_feature.check_user)
        self.assertIsNone(self.good_feature.check_date)
        self.assertEqual(self.good_feature.tags.count(), 0)

    def test_user_uncheck_permission(self):
        """User can only uncheck features that he checked."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse(
                'feature:uncheck',
                args=[self.harmful_feature_2.changeset, self.harmful_feature_2.url]
                )
            )

        self.assertEqual(response.status_code, 403)
        self.harmful_feature.refresh_from_db()
        self.assertTrue(self.harmful_feature_2.harmful)
        self.assertTrue(self.harmful_feature_2.checked)
        self.assertIsNotNone(self.harmful_feature_2.check_user)
        self.assertIsNotNone(self.harmful_feature_2.check_date)
        self.assertIn(self.tag, self.harmful_feature_2.tags.all())

    def test_try_to_uncheck_unchecked_feature(self):
        """It's not possible to uncheck an unchecked feature!"""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse(
                'feature:uncheck',
                args=[self.feature.changeset, self.feature.url]
                )
            )
        self.assertEqual(response.status_code, 403)
