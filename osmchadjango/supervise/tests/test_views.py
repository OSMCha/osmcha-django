from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import MultiPolygon, Polygon

from rest_framework.test import APIClient
from social_django.models import UserSocialAuth

from ...changeset.tests.modelfactories import ChangesetFactory
from ...users.models import User
from ..models import AreaOfInterest

client = APIClient()


class TestAoIListView(TestCase):
    def setUp(self):
        self.m_polygon = MultiPolygon(
            Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
            Polygon(((1, 1), (1, 2), (2, 2), (1, 1)))
            )
        self.m_polygon_2 = MultiPolygon(
            Polygon(((30, 30), (30, 31), (31, 31), (30, 30))),
            Polygon(((31, 31), (31, 32), (32, 32), (31, 31)))
            )
        self.user = User.objects.create_user(
            username='test_user',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user_2 = User.objects.create_user(
            username='test',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='42344',
            )
        self.area = AreaOfInterest.objects.create(
            name='Best place in the world',
            user=self.user,
            filters={'editor__icontains': 'Potlatch 2', 'harmful': 'False'},
            geometry=self.m_polygon
            )
        self.area_2 = AreaOfInterest.objects.create(
            user=self.user,
            geometry=self.m_polygon_2
            )
        self.area_3 = AreaOfInterest.objects.create(
            user=self.user_2,
            name='Harmful edits',
            filters={'harmful': 'False'},
            )
        self.url = reverse('supervise:list-create')

    def test_list_view_unauthenticated(self):
        response = client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_view(self):
        client.login(username=self.user.username, password='password')
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 2)

    def test_list_view_with_user_2(self):
        client.login(username=self.user_2.username, password='password')
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('features')), 1)
        self.assertEqual(
            response.data['features'][0]['properties']['name'],
            'Harmful edits'
            )
        self.assertEqual(
            response.data['features'][0]['properties']['filters'],
            {'harmful': 'False'}
            )


class TestAOICreateView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.url = reverse('supervise:list-create')
        self.data = {
            'filters': {'is_suspect': 'True'},
            'geometry': {
                "type": "MultiPolygon",
                "coordinates": [[[[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]]]]
                },
            'name': 'Golfo da Guiné'
            }

    def test_create_AOI_unauthenticated(self):
        response = client.post(self.url, self.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(AreaOfInterest.objects.count(), 0)

    def test_create_AOI(self):
        client.login(username=self.user.username, password='password')
        response = client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AreaOfInterest.objects.count(), 1)
        aoi = AreaOfInterest.objects.get(name='Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)
        self.assertEqual(aoi.filters, {'is_suspect': 'True'})
        self.assertTrue(
            aoi.geometry.intersects(
                Polygon(self.data['geometry']['coordinates'][0][0])
                )
            )

    def test_auto_user_field(self):
        user_2 = User.objects.create_user(
            username='test',
            email='c@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user_2,
            provider='openstreetmap',
            uid='4444',
            )
        client.login(username=self.user.username, password='password')
        self.data['user'] = user_2.username
        response = client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        aoi = AreaOfInterest.objects.get(name='Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)
