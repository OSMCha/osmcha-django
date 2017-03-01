from social_django.models import UserSocialAuth

from datetime import datetime

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Polygon

from ...users.models import User

from ..models import SuspicionReasons, Changeset

client = Client()


class TestChangesetListView(TestCase):

    def setUp(self):
        pass

    def test_changeset_home_response(self):
        response = client.get(reverse('changeset:home'))
        self.assertEqual(response.status_code, 200)


class TestChangesetDetailView(TestCase):

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
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)

    def test_changeset_detail_response(self):
        response = client.get(reverse('changeset:detail', args=[self.changeset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), 31982803)
        self.assertIn('properties', response.data.keys())
        self.assertIn('geometry', response.data.keys())


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
