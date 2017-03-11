from social_django.models import UserSocialAuth

from datetime import datetime

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Polygon

from ...users.models import User
from ..models import SuspicionReasons, Changeset
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, GoodChangesetFactory,
    HarmfulChangesetFactory
    )

client = Client()


class TestChangesetListView(TestCase):

    def setUp(self):
        SuspectChangesetFactory.create_batch(26)
        ChangesetFactory.create_batch(26)
        self.url = reverse('changeset:list')

    def test_changeset_list_response(self):
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 50)
        self.assertEqual(response.data['count'], 52)

    def test_pagination(self):
        response = client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 2)
        self.assertEqual(response.data['count'], 52)

    def test_filters(self):
        response = client.get(self.url, {'in_bbox': '-72,43,-70,45'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 52)

        response = client.get(self.url, {'in_bbox': '-3.17,-91.98,-2.1,-90.5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = client.get(self.url, {'is_suspect': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 26)

        response = client.get(self.url, {'is_suspect': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 26)


class TestChangesetListViewOrdering(TestCase):

    def setUp(self):
        SuspectChangesetFactory.create_batch(2, delete=2)
        HarmfulChangesetFactory.create_batch(24, form_create=20, modify=2, delete=40)
        GoodChangesetFactory.create_batch(24, form_create=1000, modify=20)
        self.url = reverse('changeset:list')

    def test_ordering(self):
        # default ordering is by descending id
        response = client.get(self.url)
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.all()]
            )
        # ascending id
        response = client.get(self.url, {'order_by': 'id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('id')]
            )
        # ascending date ordering
        response = client.get(self.url, {'order_by': 'date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('date')]
            )
        # descending date ordering
        response = client.get(self.url, {'order_by': '-date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-date')]
            )
        # ascending check_date
        response = client.get(self.url, {'order_by': 'check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('check_date')]
            )
        # descending check_date ordering
        response = client.get(self.url, {'order_by': '-check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-check_date')]
            )
        # ascending create ordering
        response = client.get(self.url, {'order_by': 'create'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('create')]
            )
        # descending create ordering
        response = client.get(self.url, {'order_by': '-create'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-create')]
            )
        # ascending modify ordering
        response = client.get(self.url, {'order_by': 'modify'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('modify')]
            )
        # descending modify ordering
        response = client.get(self.url, {'order_by': '-modify'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-modify')]
            )
        # ascending delete ordering
        response = client.get(self.url, {'order_by': 'delete'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('delete')]
            )
        # descending delete ordering
        response = client.get(self.url, {'order_by': '-delete'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-delete')]
            )


class TestChangesetDetailView(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = ChangesetFactory(id=31982803)
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)

    def test_changeset_detail_response(self):
        response = client.get(reverse('changeset:detail', args=[self.changeset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), 31982803)
        self.assertIn('properties', response.data.keys())
        self.assertIn('geometry', response.data.keys())
        self.assertIn('possible import', response.data['properties']['reasons'])
        self.assertIn('suspect_word', response.data['properties']['reasons'])


class TestCheckChangesetViews(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = Changeset.objects.create(
            id=31982803,
            user='test',
            uid='123123',
            editor='Potlatch 2',
            powerfull_editor=False,
            date=datetime.now(),
            create=2000,
            modify=10,
            delete=30,
            is_suspect=True,
            bbox=Polygon([
                (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
                (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
                (-71.0646843, 44.2371354)
                ])
            )
        self.changeset_2 = Changeset.objects.create(
            id=31982804,
            user='test2',
            uid='999999',
            editor='iD',
            powerfull_editor=False,
            date=datetime.now(),
            create=2000,
            modify=10,
            delete=30,
            is_suspect=True,
            bbox=Polygon([
                (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
                (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
                (-71.0646843, 44.2371354)
                ])
            )
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )

    def test_set_harmful_changeset_unlogged(self):
        response = client.get(
            reverse('changeset:set_harmful', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_unlogged(self):
        response = client.get(
            reverse('changeset:set_good', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_harmful_changeset_not_allowed(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(
            reverse('changeset:set_harmful', args=[self.changeset])
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_not_allowed(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(
            reverse('changeset:set_good', args=[self.changeset])
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_harmful_changeset_get(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:set_harmful', args=[self.changeset_2]),
            follow=True
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)

    def test_set_harmful_changeset_post(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(
            reverse('changeset:set_harmful', args=[self.changeset_2.pk]),
            follow=True
            )

        self.assertEqual(response.status_code, 200)
        changeset_2 = Changeset.objects.get(id=31982804)
        self.assertTrue(changeset_2.harmful)
        self.assertTrue(changeset_2.checked)
        self.assertEqual(changeset_2.check_user, self.user)
        self.assertIsNotNone(changeset_2.check_date)
        self.assertRedirects(
            response,
            reverse('changeset:detail', args=[changeset_2])
            )

    def test_set_good_changeset_get(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:set_good', args=[self.changeset_2]),
            follow=True
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)

    def test_set_good_changeset_post(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(
            reverse('changeset:set_good', args=[self.changeset_2]),
            follow=True
            )
        self.assertEqual(response.status_code, 200)
        changeset_2 = Changeset.objects.get(id=31982804)
        self.assertFalse(changeset_2.harmful)
        self.assertTrue(changeset_2.checked)
        self.assertEqual(changeset_2.check_user, self.user)
        self.assertIsNotNone(changeset_2.check_date)
        self.assertRedirects(
            response,
            reverse('changeset:detail', args=[changeset_2])
            )
