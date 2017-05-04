# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.contrib.gis.geos import MultiPolygon, Polygon, Point

from rest_framework.test import APITestCase
from social_django.models import UserSocialAuth

from ...changeset.tests.modelfactories import (
    ChangesetFactory, HarmfulChangesetFactory, GoodChangesetFactory,
    SuspicionReasonsFactory, TagFactory
    )
from ...feature.tests.modelfactories import FeatureFactory, CheckedFeatureFactory
from ...users.models import User
from ..models import AreaOfInterest


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
        self.assertEqual(len(response.data.get('features')), 2)

    def test_list_view_with_user_2(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.get(self.url)
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


class TestAoICreateView(APITestCase):
    def setUp(self):
        self.m_polygon = MultiPolygon(
            Polygon([[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]])
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
        self.url = reverse('supervise:aoi-list-create')
        self.data = {
            'name': 'Golfo da Guiné',
            'filters': {
                'is_suspect': 'True',
                'geometry': self.m_polygon.geojson
                },
            }
        self.data_bbox = {
            'name': 'Golfo da Guiné',
            'filters': {
                'is_suspect': 'True',
                'in_bbox': '2,0,5,2'
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
        self.assertTrue(
            aoi.geometry.intersects(
                Polygon([[2, 0], [5, 0], [5, 2], [2, 2], [2, 0]])
                )
            )

    def test_create_with_bbox(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, self.data_bbox)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AreaOfInterest.objects.count(), 1)
        aoi = AreaOfInterest.objects.get(name='Golfo da Guiné')
        self.assertEqual(aoi.user, self.user)
        self.assertEqual(aoi.filters, self.data_bbox.get('filters'))
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
        self.data['user'] = user_2.username
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

    def test_retrieve_detail(self):
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
        response = self.client.put(
            reverse('supervise:aoi-detail', args=[self.aoi.pk]),
            self.data
            )
        self.assertEqual(response.status_code, 401)
        self.aoi.refresh_from_db()
        self.assertEqual(self.aoi.name, 'Best place in the world')

    def test_delete_aoi_unauthenticated(self):
        response = self.client.delete(
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
        self.client.login(username=user.username, password='password')
        response = self.client.put(
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
        self.client.login(username=user.username, password='password')
        response = self.client.delete(
            reverse('supervise:aoi-detail', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AreaOfInterest.objects.count(), 1)

    def test_update_with_aoi_owner_user(self):
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

    def test_put_empty_geometry(self):
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
        self.assertTrue(
            self.aoi.geometry.intersects(
                Polygon(((4, 0), (5, 0), (5, 1), (4, 0)))
                )
            )

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


class TestAoIChangesetAndFeatureListViews(APITestCase):
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
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 50)
        self.assertIn('features', response.data.keys())
        self.assertIn('geometry', response.data['features'][0].keys())
        self.assertIn('properties', response.data['features'][0].keys())

        # test pagination
        response = self.client.get(
            reverse('supervise:aoi-list-changesets', args=[self.aoi.pk]),
            {'page': 2}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 1)

    def test_aoi_list_features_view(self):
        CheckedFeatureFactory(harmful=False)
        CheckedFeatureFactory(geometry=Point(0.5, 0.5))
        CheckedFeatureFactory.create_batch(
            51, geometry=Point(0.5, 0.5), harmful=False
            )
        response = self.client.get(
            reverse('supervise:aoi-list-features', args=[self.aoi.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 50)
        self.assertIn('features', response.data.keys())
        self.assertIn('geometry', response.data['features'][0].keys())
        self.assertIn('properties', response.data['features'][0].keys())

        # test pagination
        response = self.client.get(
            reverse('supervise:aoi-list-features', args=[self.aoi.pk]),
            {'page': 2}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['features']), 1)


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
        self.assertIn(
            {'name': 'possible import', 'checked_changesets': 5, 'harmful_changesets': 0},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'Vandalism', 'checked_changesets': 5, 'harmful_changesets': 0},
            response.data.get('tags')
            )

    def test_stats_with_staff_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('checked_changesets'), 51)
        self.assertEqual(response.data.get('harmful_changesets'), 0)
        self.assertEqual(response.data.get('users_with_harmful_changesets'), 0)
        self.assertEqual(len(response.data.get('reasons')), 2)
        self.assertEqual(len(response.data.get('tags')), 2)
        self.assertIn(
            {'name': 'possible import', 'checked_changesets': 5, 'harmful_changesets': 0},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'Mass Deletion', 'checked_changesets': 5, 'harmful_changesets': 0},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'Vandalism', 'checked_changesets': 5, 'harmful_changesets': 0},
            response.data.get('tags')
            )
        self.assertIn(
            {'name': 'Big buildings', 'checked_changesets': 5, 'harmful_changesets': 0},
            response.data.get('tags')
            )
