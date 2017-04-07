# -*- coding: utf-8 -*-
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
        self.url = reverse('supervise:aoi-list-create')

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
        self.url = reverse('supervise:aoi-list-create')
        self.data = {
            'filters': {'is_suspect': 'True'},
            'geometry': {
                "type": "MultiPolygon",
                "coordinates": [[[[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]]]]
                },
            'name': u'Golfo da Guiné'
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
        aoi = AreaOfInterest.objects.get(name=u'Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)
        self.assertEqual(aoi.filters, {'is_suspect': 'True'})
        self.assertTrue(
            aoi.geometry.intersects(
                Polygon(self.data['geometry']['coordinates'][0][0])
                )
            )

    def test_validation(self):
        client.login(username=self.user.username, password='password')
        response = client.post(self.url, {'name': 'Empty AoI'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AreaOfInterest.objects.count(), 0)

        # test validation of unique name of AoI for each user
        response = client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        response = client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)

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
        aoi = AreaOfInterest.objects.get(name=u'Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)


class TestAOIDetailAPIViews(TestCase):
    def setUp(self):
        self.m_polygon = MultiPolygon(
            Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
            Polygon(((1, 1), (1, 2), (2, 2), (1, 1)))
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
        self.aoi = AreaOfInterest.objects.create(
            name='Best place in the world',
            user=self.user,
            filters={'editor__icontains': 'Potlatch 2', 'harmful': 'False'},
            geometry=self.m_polygon
            )
        self.data = {
            'filters': {'is_suspect': 'True'},
            'geometry': {
                "type": "MultiPolygon",
                "coordinates": [[[[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]]]]
                },
            'name': u'Golfo da Guiné'
            }

    def test_retrieve_detail(self):
        response = client.get(reverse('supervise:aoi-detail', args=[self.aoi.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['properties']['name'],
            'Best place in the world'
            )
        self.assertEqual(
            response.data['properties']['filters'],
            {'editor__icontains': 'Potlatch 2', 'harmful': 'False'}
            )
        self.assertEqual(
            response.data['geometry']['type'],
            'MultiPolygon'
            )
        self.assertIn(
            'id',
            response.data.keys()
            )
        self.assertNotIn(
            'user',
            response.data.keys()
            )
        self.assertEqual(
            response.data['properties']['changesets_url'],
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk])
            )

    def test_update_aoi_unauthenticated(self):
        response = client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 401)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

    def test_delete_aoi_unauthenticated(self):
        response = client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(AreaOfInterest.objects.count(), 1)

    def test_update_aoi_of_another_user(self):
        user = User.objects.create_user(
            username='test_2',
            email='c@a.com',
            password='password'
            )
        client.login(username=user.username, password='password')
        response = client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 403)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

    def test_delete_aoi_of_another_user(self):
        user = User.objects.create_user(
            username='test_2',
            email='c@a.com',
            password='password'
            )
        client.login(username=user.username, password='password')
        response = client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AreaOfInterest.objects.count(), 1)

    def test_update_with_aoi_owner_user(self):
        client.login(username=self.user.username, password='password')
        response = client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, u'Golfo da Guiné')
        self.assertEqual(self.aoi.filters, {'is_suspect': 'True'})
        self.assertTrue(
            self.aoi.geometry.intersects(
                Polygon(((4, 0), (5, 0), (5, 1), (4, 0)))
                )
            )

    def test_validation(self):
        client.login(username=self.user.username, password='password')
        response = client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 200)

        # validate if the user are not allowed to let the filters and geometry fields empty
        response = client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            {'name': u'Golfo da Guiné'}
            )
        self.assertEqual(response.status_code, 400)
        self.aoi.refresh_from_db()
        self.assertIsNotNone(self.aoi.filters)
        self.assertIsNotNone(self.aoi.geometry)

    def test_delete_with_aoi_owner_user(self):
        client.login(username=self.user.username, password='password')
        response = client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(AreaOfInterest.objects.count(), 0)

    def test_aoi_list_changesets_view(self):
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        ChangesetFactory(
            editor='JOSM 1.5',
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        ChangesetFactory.create_batch(
            51,
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        response = client.get(
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 50)
        self.assertIn('features', response.data.keys())
        self.assertIn('geometry', response.data['features'][0].keys())
        self.assertIn('properties', response.data['features'][0].keys())

        # test pagination
        response = client.get(
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk]),
            {'page': 2}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 1)
