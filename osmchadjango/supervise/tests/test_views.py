# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import xml.etree.ElementTree as ET

from django.urls import reverse
from django.contrib.gis.geos import MultiPolygon, Polygon, Point, LineString

from rest_framework.test import APITestCase
from social_django.models import UserSocialAuth

from ...changeset.tests.modelfactories import (
    ChangesetFactory, HarmfulChangesetFactory, GoodChangesetFactory,
    SuspicionReasonsFactory, TagFactory, UserWhitelistFactory
    )
from ...users.models import User
from ..models import AreaOfInterest, BlacklistedUser


class TestAoIListView(APITestCase):
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
            geometry=self.m_polygon,
            filters={
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'geometry': self.m_polygon.geojson
                },
            )
        self.area_2 = AreaOfInterest.objects.create(
            name='Another AOI',
            user=self.user,
            filters={'geometry': self.m_polygon_2.geojson},
            geometry=self.m_polygon_2
            )
        self.area_3 = AreaOfInterest.objects.create(
            user=self.user_2,
            name='Harmful edits',
            filters={'harmful': 'False'},
            )
        self.url = reverse('supervise:aoi-list-create')

    def test_list_view_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_view(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results').get('features')), 2)

    def test_ordering(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # test default ordering is -date
        self.assertEqual(
            response.data.get('results').get('features')[0]['properties']['name'],
            'Another AOI'
            )
        # test ordering by date
        response = self.client.get(self.url, {'order_by': 'date'})
        self.assertEqual(
            response.data.get('results').get('features')[0]['properties']['name'],
            'Best place in the world'
            )
        # test ordering by name
        response = self.client.get(self.url, {'order_by': '-name'})
        self.assertEqual(
            response.data.get('results').get('features')[0]['properties']['name'],
            'Best place in the world'
            )

    def test_list_view_with_user_2(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results').get('features')), 1)
        self.assertEqual(
            response.data.get('results')['features'][0]['properties']['name'],
            'Harmful edits'
            )
        self.assertEqual(
            response.data.get('results')['features'][0]['properties']['filters'],
            {'harmful': 'False'}
            )


class TestAoICreateView(APITestCase):
    def setUp(self):
        self.polygon = Polygon([[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]])
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
            'name': 'Golfo da Guiné',
            'filters': {
                'is_suspect': 'True',
                'geometry': self.polygon.geojson
                },
            }
        self.data_bbox = {
            'name': 'Golfo da Guiné',
            'filters': {
                'is_suspect': 'True',
                'in_bbox': '2,0,5,2'
                },
            }
        self.without_geo_aoi = {
            'name': 'Unchecked suspect changesets',
            'filters': {
                'is_suspect': 'True',
                'checked': 'False'
                },
            }

    def test_create_AOI_unauthenticated(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(AreaOfInterest.objects.count(), 0)

    def test_create_AOI(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AreaOfInterest.objects.count(), 1)
        aoi = AreaOfInterest.objects.get(name='Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)
        self.assertEqual(aoi.filters, self.data.get('filters'))
        self.assertIsInstance(aoi.geometry, Polygon)
        self.assertTrue(
            aoi.geometry.intersects(
                Polygon([[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]])
                )
            )

    def test_create_without_geometry_and_bbox(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, self.without_geo_aoi)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AreaOfInterest.objects.count(), 1)
        aoi = AreaOfInterest.objects.get(name='Unchecked suspect changesets')
        self.assertEqual(aoi.user, self.user)
        self.assertEqual(aoi.filters, self.without_geo_aoi.get('filters'))

    def test_create_with_bbox(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, self.data_bbox)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AreaOfInterest.objects.count(), 1)
        aoi = AreaOfInterest.objects.get(name='Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)
        self.assertEqual(aoi.filters, self.data_bbox.get('filters'))
        self.assertIsInstance(aoi.geometry, Polygon)
        self.assertTrue(
            aoi.geometry.intersects(
                Polygon([[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]])
                )
            )

    def test_validation(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, {'name': 'Empty AoI'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AreaOfInterest.objects.count(), 0)

        # test validation of unique name of AoI for each user
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.url, self.data)
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
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        aoi = AreaOfInterest.objects.get(name='Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)


class TestAoIDetailAPIViews(APITestCase):
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
            geometry=self.m_polygon,
            filters={
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'users': 'test',
                'uids': '234,43',
                'checked_by': 'qa_user',
                'geometry': self.m_polygon.geojson
                },
            )
        self.m_polygon_2 = MultiPolygon(
            Polygon([[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]])
            )
        self.data = {
            'filters': {
                'is_suspect': 'True',
                'geometry': self.m_polygon_2.geojson,
                },
            'name': 'Golfo da Guiné'
            }

    def test_unauthenticated(self):
        response = self.client.get(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 401)

    def test_retrieve_detail_authenticated(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['properties']['name'],
            'Best place in the world'
            )
        self.assertEqual(
            response.data['properties']['filters'],
            {
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'users': 'test',
                'uids': '234,43',
                'checked_by': 'qa_user',
                'geometry': self.m_polygon.geojson
            }
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
        """Unauthenticated users can not update AoI"""
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 401)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

        response = self.client.patch(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 401)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

    def test_delete_aoi_unauthenticated(self):
        """Unauthenticated users can not delete AoI"""
        response = self.client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(AreaOfInterest.objects.count(), 1)

    def test_update_aoi_of_another_user(self):
        """A user can not update AoI of another user."""
        user = User.objects.create_user(
            username='test_2',
            email='c@a.com',
            password='password'
            )
        self.client.login(username=user.username, password='password')
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 403)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

        response = self.client.patch(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 403)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

    def test_delete_aoi_of_another_user(self):
        """A user can not delete AoI of another user."""
        user = User.objects.create_user(
            username='test_2',
            email='c@a.com',
            password='password'
            )
        self.client.login(username=user.username, password='password')
        response = self.client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AreaOfInterest.objects.count(), 1)

    def test_update_with_aoi_owner_user(self):
        """User can update his/her AoI"""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Golfo da Guiné')
        self.assertEqual(self.aoi.filters, self.data.get('filters'))
        self.assertTrue(
            self.aoi.geometry.intersects(
                Polygon(((4, 0), (5, 0), (5, 1), (4, 0)))
                )
            )

    def test_put_update_with_bbox(self):
        """'in_bbox' field must populate the geometry field with a Polygon"""
        data = {
            'filters': {
                'is_suspect': 'True',
                'in_bbox': '4,0,5,1'
                },
            'name': 'Golfo da Guiné'
            }
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Golfo da Guiné')
        self.assertEqual(self.aoi.filters, data.get('filters'))
        self.assertTrue(
            self.aoi.geometry.intersects(
                Polygon(((4, 0), (5, 0), (5, 1), (4, 0)))
                )
            )
        self.assertIsInstance(self.aoi.geometry, Polygon)

    def test_put_empty_geometry(self):
        """If the AoI receives a filter without geometry and in_bbox information,
        the geometry field will be updated to None."""
        data = {
            'filters': {
                'is_suspect': 'True',
                },
            'name': 'Golfo da Guiné'
            }
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Golfo da Guiné')
        self.assertEqual(self.aoi.filters, data.get('filters'))
        self.assertIsNone(self.aoi.geometry)

    def test_patch_empty_geometry(self):
        """If the AoI receives a filter without geometry and in_bbox information,
        the geometry field will be updated to None."""
        data = {
            'filters': {
                'is_suspect': 'True',
                },
            'name': 'Golfo da Guiné'
            }
        self.client.login(username=self.user.username, password='password')
        response = self.client.patch(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Golfo da Guiné')
        self.assertEqual(self.aoi.filters, data.get('filters'))
        self.assertIsNone(self.aoi.geometry)

    def test_patch_update_with_bbox(self):
        """'in_bbox' field must populate the geometry field with a Polygon"""
        data = {
            'filters': {
                'is_suspect': 'True',
                'in_bbox': '4,0,5,1'
                }
            }
        self.client.login(username=self.user.username, password='password')
        response = self.client.patch(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.filters, data.get('filters'))
        self.assertIsInstance(self.aoi.geometry, Polygon)
        self.assertTrue(
            self.aoi.geometry.intersects(
                Polygon(((4, 0), (5, 0), (5, 1), (4, 0)))
                )
            )

    def test_update_with_line_and_point(self):
        """The geometry field must receive any geometry type."""
        point = Point((0.5, 0.5))
        data = {
            'filters': {
                'geometry': point.geojson,
                },
            'name': 'Golfo da Guiné'
            }
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertIsInstance(self.aoi.geometry, Point)

        line = LineString(((0.5, 0.5), (1, 1)))
        data = {
            'filters': {
                'geometry': line.geojson,
                },
            'name': 'Golfo da Guiné'
            }
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.aoi.refresh_from_db()
        self.assertIsInstance(self.aoi.geometry, LineString)

    def test_validation(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 200)

        # validate if the user are not allowed to let the filters and geometry fields empty
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            {'name': 'Golfo da Guiné'}
            )
        self.assertEqual(response.status_code, 400)
        self.aoi.refresh_from_db()
        self.assertIsNotNone(self.aoi.filters)
        self.assertIsNotNone(self.aoi.geometry)

    def test_delete_with_aoi_owner_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(AreaOfInterest.objects.count(), 0)


class TestAoIChangesetListView(APITestCase):
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
            geometry=self.m_polygon,
            filters={
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'geometry': self.m_polygon.geojson
                },
            )

    def test_authenticated_aoi_list_changesets_view(self):
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

        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 50)
        self.assertIn('features', response.data.keys())
        self.assertIn('geometry', response.data['features'][0].keys())
        self.assertIn('properties', response.data['features'][0].keys())
        self.assertIn('check_user', response.data['features'][0]['properties'])
        self.assertIn('user', response.data['features'][0]['properties'])
        self.assertIn('uid', response.data['features'][0]['properties'])

    def test_unauthenticated_aoi_list_changesets_view(self):
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 401)

    def test_aoi_with_in_bbox_filter(self):
        aoi_with_in_bbox = AreaOfInterest.objects.create(
            name='Another place in the world',
            user=self.user,
            geometry=Polygon(((0, 0), (0, 2), (2, 2), (2, 0), (0, 0))),
            filters={
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'in_bbox': '0,0,2,2'
                },
            )
        ChangesetFactory(
            harmful=False,
            bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10)))
            )
        ChangesetFactory(
            editor='JOSM 1.5',
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        ChangesetFactory.create_batch(
            51,
            harmful=False,
            bbox=Polygon(((10, 10), (10, 10.5), (10.7, 10.5), (10, 10))),
            )
        ChangesetFactory.create_batch(
            51,
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )

        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi_with_in_bbox.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 50)

    def test_aoi_with_hide_whitelist_filter(self):
        aoi = AreaOfInterest.objects.create(
            name='Another place in the world',
            user=self.user,
            filters={
                'editor': 'Potlatch 2',
                'hide_whitelist': 'True'
                },
            )
        user_2 = User.objects.create_user(
            username='user_2',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user_2,
            provider='openstreetmap',
            uid='42344',
            )
        UserWhitelistFactory(user=self.user, whitelist_user='test')
        UserWhitelistFactory(user=user_2, whitelist_user='other_user')
        UserWhitelistFactory(user=user_2, whitelist_user='another_user')
        ChangesetFactory()
        ChangesetFactory(user='other_user', uid='333')
        ChangesetFactory(user='another_user', uid='4333')

        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['features']), 2)
        self.client.logout()

        # test with a second user to assure the results of the hide_whitelist filter
        # are the same, it doesn't matter the user that is accessing
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['features']), 2)

    def test_aoi_with_false_hide_whitelist_filter(self):
        aoi = AreaOfInterest.objects.create(
            name='Another place in the world',
            user=self.user,
            filters={
                'editor': 'Potlatch 2',
                'hide_whitelist': 'False'
                },
            )
        user_2 = User.objects.create_user(
            username='user_2',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user_2,
            provider='openstreetmap',
            uid='42344',
            )
        UserWhitelistFactory(user=self.user, whitelist_user='test')
        UserWhitelistFactory(user=user_2, whitelist_user='other_user')
        UserWhitelistFactory(user=user_2, whitelist_user='another_user')
        ChangesetFactory()
        ChangesetFactory(user='other_user', uid='333')
        ChangesetFactory(user='another_user', uid='4333')

        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['features']), 3)
        self.client.logout()

        # test with a second user to assure the results of the hide_whitelist=False
        # filter are the same, it doesn't matter the user that is accessing
        self.client.login(username=user_2.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['features']), 3)

    def test_aoi_with_blacklist_filter(self):
        aoi = AreaOfInterest.objects.create(
            name='Another place in the world',
            user=self.user,
            filters={
                'editor': 'Potlatch 2',
                'blacklist': 'True'
                },
            )
        BlacklistedUser.objects.create(
            username='test',
            uid='123123',
            added_by=self.user,
            )
        user_2 = User.objects.create_user(
            username='user_2',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user_2,
            provider='openstreetmap',
            uid='42344',
            )
        BlacklistedUser.objects.create(
            username='other_user',
            uid='333',
            added_by=user_2,
            )
        BlacklistedUser.objects.create(
            username='another_user',
            uid='4333',
            added_by=user_2,
            )
        ChangesetFactory()
        ChangesetFactory(user='other_user', uid='333')
        ChangesetFactory(user='another_user', uid='4333')
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['features']), 1)
        self.client.logout()

        # test with a second user to assure the results of the blacklist filter
        # are the same, it doesn't matter the user that is accessing
        self.client.login(username=user_2.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['features']), 1)

    def test_aoi_with_false_blacklist_filter(self):
        aoi = AreaOfInterest.objects.create(
            name='Another place in the world',
            user=self.user,
            filters={
                'editor': 'Potlatch 2',
                'blacklist': 'False'
                },
            )
        BlacklistedUser.objects.create(
            username='test',
            uid='123123',
            added_by=self.user,
            )
        user_2 = User.objects.create_user(
            username='user_2',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user_2,
            provider='openstreetmap',
            uid='42344',
            )
        BlacklistedUser.objects.create(
            username='other_user',
            uid='333',
            added_by=user_2,
            )
        BlacklistedUser.objects.create(
            username='another_user',
            uid='4333',
            added_by=user_2,
            )
        ChangesetFactory()
        ChangesetFactory(user='other_user', uid='333')
        ChangesetFactory(user='another_user', uid='4333')

        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['features']), 3)
        self.client.logout()

        self.client.login(username=user_2.username, password='password')
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['features']), 3)

    def test_aoi_changesets_feed_view(self):
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        ChangesetFactory(
            editor='JOSM 1.5',
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        GoodChangesetFactory.create_batch(
            51,
            comment='Test case',
            user='çãoéí',
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        response = self.client.get(
            reverse('supervise:aoi-changesets-feed', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        rss_data = ET.fromstring(response.content).getchildren()[0].getchildren()
        title = [i for i in rss_data if i.tag == 'title'][0]
        items = [i for i in rss_data if i.tag == 'item']
        link = [i for i in items[0].getchildren() if i.tag == 'link'][0]
        self.assertIn(
            "?aoi=",
            link.text
            )
        self.assertEqual(
            title.text,
            'Changesets of Area of Interest {} by {}'.format(
                self.aoi.name, self.aoi.user.username
                )
            )
        self.assertEqual(len(items), 50)

    def test_feed_view_of_unnamed_aoi_and_zero_changesets(self):
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        HarmfulChangesetFactory(
            editor='JOSM 1.5',
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        self.aoi.name = ''
        self.aoi.filters = {
            'editor': 'JOSM 1.5',
            'harmful': 'True',
            'in_bbox': '0,0,2,2'
            }
        self.aoi.save()

        response = self.client.get(
            reverse('supervise:aoi-changesets-feed', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        rss_data = ET.fromstring(response.content).getchildren()[0].getchildren()
        title = [i for i in rss_data if i.tag == 'title'][0]
        items = [i for i in rss_data if i.tag == 'item']
        self.assertEqual(
            title.text,
            'Changesets of Area of Interest Unnamed by {}'.format(
                self.aoi.user.username
                )
            )
        self.assertEqual(len(items), 1)

    def test_feed_view_of_aoi_with_blacklist_filter(self):
        BlacklistedUser.objects.create(
            username='test_1',
            uid='123123',
            added_by=self.user,
            )
        ChangesetFactory(
            user="test_2",
            editor='JOSM 1.5',
            bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10)))
            )
        HarmfulChangesetFactory(
            user="test_1",
            editor='JOSM 1.5',
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0)))
            )
        self.aoi.name = ''
        self.aoi.filters = {
            'editor': 'JOSM 1.5',
            'blacklist': 'True',
            }
        self.aoi.save()

        response = self.client.get(
            reverse('supervise:aoi-changesets-feed', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        rss_data = ET.fromstring(response.content).getchildren()[0].getchildren()
        title = [i for i in rss_data if i.tag == 'title'][0]
        items = [i for i in rss_data if i.tag == 'item']
        self.assertEqual(
            title.text,
            'Changesets of Area of Interest Unnamed by {}'.format(
                self.aoi.user.username
                )
            )
        self.assertEqual(len(items), 1)

    def test_feed_view_of_aoi_with_hide_whitelist_filter(self):
        aoi = AreaOfInterest.objects.create(
            name='Another place in the world',
            user=self.user,
            filters={
                'editor': 'Potlatch 2',
                'hide_whitelist': 'True'
                },
            )
        UserWhitelistFactory(user=self.user, whitelist_user='test')
        ChangesetFactory()
        ChangesetFactory(user='other_user', uid='333')
        ChangesetFactory(user='another_user', uid='4333')


        response = self.client.get(
            reverse('supervise:aoi-changesets-feed', args=[aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        rss_data = ET.fromstring(response.content).getchildren()[0].getchildren()
        title = [i for i in rss_data if i.tag == 'title'][0]
        items = [i for i in rss_data if i.tag == 'item']
        self.assertEqual(
            title.text,
            'Changesets of Area of Interest Another place in the world by {}'.format(
                self.aoi.user.username
                )
            )
        self.assertEqual(len(items), 2)


class TestAoIStatsAPIViews(APITestCase):
    def setUp(self):
        self.m_polygon = MultiPolygon(
            Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
            Polygon(((1, 1), (1, 2), (2, 2), (1, 1)))
            )
        self.user = User.objects.create_user(
            username='test_user',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.aoi = AreaOfInterest.objects.create(
            name='Best place in the world',
            user=self.user,
            geometry=self.m_polygon,
            filters={
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'geometry': self.m_polygon.geojson
                },
            )
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        HarmfulChangesetFactory(
            editor='JOSM 1.5',
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        self.good_changesets = GoodChangesetFactory.create_batch(
            51,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        self.reason = SuspicionReasonsFactory(name='possible import')
        self.reason_2 = SuspicionReasonsFactory(
            name='Mass Deletion', is_visible=False)
        self.reason.changesets.set(self.good_changesets[0:5])
        self.reason_2.changesets.set(self.good_changesets[5:10])
        self.tag_1 = TagFactory(name='Vandalism')
        self.tag_2 = TagFactory(name='Big buildings', is_visible=False)
        self.tag_1.changesets.set(self.good_changesets[0:5])
        self.tag_2.changesets.set(self.good_changesets[5:10])
        self.url = reverse('supervise:aoi-stats', args=[self.aoi.pk])

    def test_stats_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('checked_changesets'), 51)
        self.assertEqual(response.data.get('harmful_changesets'), 0)
        self.assertEqual(response.data.get('users_with_harmful_changesets'), 0)
        self.assertEqual(len(response.data.get('reasons')), 1)
        self.assertEqual(len(response.data.get('tags')), 1)
        possible_import = {
            'name': 'possible import',
            'changesets': 5,
            'checked_changesets': 5,
            'harmful_changesets': 0
            }
        self.assertIn(possible_import, response.data.get('reasons'))
        vandalism = {
            'name': 'Vandalism',
            'changesets': 5,
            'checked_changesets': 5,
            'harmful_changesets': 0
            }
        self.assertIn(vandalism, response.data.get('tags'))

    def test_stats_with_staff_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('checked_changesets'), 51)
        self.assertEqual(response.data.get('harmful_changesets'), 0)
        self.assertEqual(response.data.get('users_with_harmful_changesets'), 0)
        self.assertEqual(len(response.data.get('reasons')), 2)
        self.assertEqual(len(response.data.get('tags')), 2)

        possible_import = {
            'name': 'possible import',
            'changesets': 5,
            'checked_changesets': 5,
            'harmful_changesets': 0
            }
        self.assertIn(possible_import, response.data.get('reasons'))

        vandalism = {
            'name': 'Vandalism',
            'changesets': 5,
            'checked_changesets': 5,
            'harmful_changesets': 0
            }
        self.assertIn(vandalism, response.data.get('tags'))

        mass_deletion = {
            'name': 'Mass Deletion',
            'changesets': 5,
            'checked_changesets': 5,
            'harmful_changesets': 0
            }
        self.assertIn(mass_deletion, response.data.get('reasons'))

        big_buildings = {
            'name': 'Big buildings',
            'changesets': 5,
            'checked_changesets': 5,
            'harmful_changesets': 0
            }
        self.assertIn(big_buildings, response.data.get('tags'))


class TestBlacklistedUserListAPIView(APITestCase):
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
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='999898',
            )
        BlacklistedUser.objects.create(
            username='Bad User',
            uid='3434',
            added_by=self.staff_user,
            )
        BlacklistedUser.objects.create(
            username='Vandal',
            uid='3435',
            added_by=self.staff_user,
            )
        BlacklistedUser.objects.create(
            username='New bad user',
            uid='9888',
            added_by=self.user,
            )
        self.url = reverse('supervise:blacklist-list-create')

    def test_list_view_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_view_normal_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)

    def test_list_view_staff_user(self):
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 2)


class TestBlacklistedUserCreateAPIView(APITestCase):
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
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='999898',
            )
        self.url = reverse('supervise:blacklist-list-create')
        self.data = {'username': 'Bad User', 'uid': '3434'}

    def test_create_view_unauthenticated(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(BlacklistedUser.objects.count(), 0)

    def test_create_view_normal_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BlacklistedUser.objects.count(), 1)

    def test_create_view_staff_user(self):
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BlacklistedUser.objects.count(), 1)


class TestBlacklistedUserDetailAPIViews(APITestCase):
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
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='999898',
            )

        self.blacklisted = BlacklistedUser.objects.create(
            username='Bad User',
            uid='3434',
            added_by=self.staff_user,
            )
        self.blacklisted_2 = BlacklistedUser.objects.create(
            username='Bad User',
            uid='3434',
            added_by=self.user,
            )
        self.url = reverse(
            'supervise:blacklist-detail', args=[self.blacklisted.uid]
            )

    def test_unauthenticated_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_normal_user_get(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('username'), 'Bad User')
        self.assertEqual(response.data.get('added_by'), 'test_user')
        self.assertIsNotNone(response.data.get('uid'))
        self.assertIn('date', response.data.keys())

    def test_normal_user_getting_staff_user_blacklist(self):
        blacklisted = BlacklistedUser.objects.create(
            username='Bad User',
            uid='4999',
            added_by=self.staff_user,
            )
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('supervise:blacklist-detail', args=[4999])
            )
        self.assertEqual(response.status_code, 404)

    def test_staff_user_get(self):
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('username'), 'Bad User')
        self.assertEqual(response.data.get('added_by'), 'staff_user')
        self.assertIsNotNone(response.data.get('uid'))
        self.assertIn('date', response.data.keys())

    def test_unauthenticated_delete(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(BlacklistedUser.objects.count(), 2)

    def test_normal_user_delete(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(BlacklistedUser.objects.count(), 1)

    def test_staff_user_delete(self):
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(BlacklistedUser.objects.count(), 1)

    def test_unauthenticated_patch(self):
        response = self.client.patch(self.url, {'username': 'other_user'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.blacklisted.username, 'Bad User')

    def test_normal_user_patch(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.patch(self.url, {'username': 'other_user'})
        self.assertEqual(response.status_code, 200)
        self.blacklisted_2.refresh_from_db()
        self.assertEqual(self.blacklisted_2.username, 'other_user')

    def test_staff_user_patch(self):
        self.client.login(username=self.staff_user.username, password='password')
        response = self.client.patch(self.url, {'username': 'other_user'})
        self.assertEqual(response.status_code, 200)
        self.blacklisted.refresh_from_db()
        self.assertEqual(self.blacklisted.username, 'other_user')
