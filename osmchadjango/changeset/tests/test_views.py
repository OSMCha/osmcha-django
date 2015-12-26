from social.apps.django_app.default.models import UserSocialAuth

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
        self.changeset2 = Changeset.objects.create(
            id=31982803,
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
        self.user = User.objects.create(username='test', password='pass',
            email='a@a.com')
        UserSocialAuth(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
        )

    def set_harmfull_changeset_unlogged(self):
        self.assertIsNone(self.changeset.harmfull)

        response = client.get(
            reverse('changeset:set_harmfull', args=[self.changeset])
        )
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(self.changeset.harmfull)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def set_harmfull_changeset_not_allowed(self):
        response = client.post(
            reverse('changeset:set_harmfull', args=[self.changeset])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.changeset.harmfull)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)
        self.assertTemplateUsed(response, 'changeset/not_allowed.html')

    def set_harmfull_changeset(self):
        self.assertIsNone(self.changeset.harmfull)
        client.login(self.user.username, 'pass')

        response = client.get(
            reverse('changeset:set_harmfull', args=[self.changeset2])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.changeset.harmfull)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)
        self.assertTemplateUsed(response, 'changeset/confirm_harmfull.html')

        response = client.post(
            reverse('changeset:set_harmfull', args=[self.changeset2])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.changeset.harmfull)
        self.assertTrue(self.changeset.checked)
        self.assertEqual(self.changeset.check_user, self.user)
        self.assertIsNotNone(self.changeset.check_date)
        self.assertRedirects(
            response,
            reverse('changeset:detail', args=[self.changeset2.pk])
        )
