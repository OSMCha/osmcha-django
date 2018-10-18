from django.urls import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ..models import SuspicionReasons, Tag
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, GoodChangesetFactory,
    HarmfulChangesetFactory
    )


class TestStatsView(APITestCase):
    def setUp(self):
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
        self.changeset = ChangesetFactory()
        self.suspect_changeset = SuspectChangesetFactory()
        self.harmful_changeset = HarmfulChangesetFactory(user='another_user')
        self.harmful_changeset_2 = HarmfulChangesetFactory()
        self.good_changeset = GoodChangesetFactory()
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.reason_3 = SuspicionReasons.objects.create(
            name='vandalism in my city', is_visible=False)
        self.reason_1.changesets.set(
            [self.suspect_changeset, self.harmful_changeset, self.changeset]
            )
        self.reason_2.changesets.set(
            [self.harmful_changeset_2, self.good_changeset]
            )
        self.reason_3.changesets.set(
            [self.harmful_changeset_2, self.good_changeset]
            )
        self.tag_1 = Tag.objects.create(name='Vandalism')
        self.tag_2 = Tag.objects.create(name='Minor errors')
        self.tag_3 = Tag.objects.create(name='Big buildings', is_visible=False)
        self.tag_1.changesets.set(
            [self.harmful_changeset, self.harmful_changeset_2, self.changeset]
            )
        self.tag_2.changesets.add(self.good_changeset)
        self.tag_3.changesets.set(
            [self.harmful_changeset, self.harmful_changeset_2, self.good_changeset]
            )
        self.url = reverse('changeset:stats')

    def test_stats_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        results = response.data.get('results')
        self.assertEqual(results.get('changesets'), 5)
        self.assertEqual(results.get('checked_changesets'), 3)
        self.assertEqual(results.get('harmful_changesets'), 2)
        self.assertEqual(results.get('users_with_harmful_changesets'), 2)
        self.assertEqual(len(results.get('reasons')), 2)
        self.assertEqual(len(results.get('tags')), 2)
        possible_import = {
            'name': 'possible import',
            'changesets': 3,
            'checked_changesets': 1,
            'harmful_changesets': 1
            }
        self.assertIn(possible_import, results.get('reasons'))
        suspect_word = {
            'name': 'suspect_word',
            'changesets': 2,
            'checked_changesets': 2,
            'harmful_changesets': 1
            }
        self.assertIn(suspect_word, results.get('reasons'))
        vandalism = {
            'name': 'Vandalism',
            'changesets': 3,
            'checked_changesets': 2,
            'harmful_changesets': 2
            }
        self.assertIn(vandalism, results.get('tags'))
        minor_errors = {
            'name': 'Minor errors',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 0
            }
        self.assertIn(minor_errors, results.get('tags'))

    def test_stats_view_with_filters(self):
        response = self.client.get(self.url, {'harmful': False})
        self.assertEqual(response.status_code, 200)
        results = response.data.get('results')
        self.assertEqual(results.get('changesets'), 1)
        self.assertEqual(results.get('checked_changesets'), 1)
        self.assertEqual(results.get('harmful_changesets'), 0)
        self.assertEqual(results.get('users_with_harmful_changesets'), 0)
        self.assertEqual(len(results.get('reasons')), 2)
        self.assertEqual(len(results.get('tags')), 2)

        possible_import = {
            'name': 'possible import',
            'changesets': 0,
            'checked_changesets': 0,
            'harmful_changesets': 0
            }
        self.assertIn(possible_import, results.get('reasons'))

        suspect_word = {
            'name': 'suspect_word',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 0
            }
        self.assertIn(suspect_word, results.get('reasons'))

        vandalism = {
            'name': 'Vandalism',
            'changesets': 0,
            'checked_changesets': 0,
            'harmful_changesets': 0
            }
        self.assertIn(vandalism, results.get('tags'))

        minor_errors = {
            'name': 'Minor errors',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 0
            }
        self.assertIn(minor_errors, results.get('tags'))

    def test_stats_view_with_staff_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        results = response.data.get('results')
        self.assertEqual(len(results.get('reasons')), 3)
        self.assertEqual(len(results.get('tags')), 3)
        vandalism_city = {
            'name': 'vandalism in my city',
            'changesets': 2,
            'checked_changesets': 2,
            'harmful_changesets': 1
            }
        self.assertIn(vandalism_city, results.get('reasons'))
        big_buildings = {
            'name': 'Big buildings',
            'changesets': 3,
            'checked_changesets': 3,
            'harmful_changesets': 2
            }
        self.assertIn(big_buildings, results.get('tags'))


class TestUserStatsViews(APITestCase):
    def setUp(self):
        GoodChangesetFactory(user='user_one', uid='4321')
        HarmfulChangesetFactory(user='user_one', uid='4321')
        SuspectChangesetFactory(user='user_one', uid='4321')
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

    def test_unauthenticated_request(self):
        response = self.client.get(reverse('changeset:user-stats', args=['4321']))
        self.assertEqual(response.status_code, 401)

    def test_user_one_stats(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:user-stats', args=['4321']))
        self.assertEqual(response.status_code, 200)
        results = response.data.get('results')
        self.assertEqual(results.get('changesets_in_osmcha'), 3)
        self.assertEqual(results.get('checked_changesets'), 2)
        self.assertEqual(results.get('harmful_changesets'), 1)

    def test_user_without_changesets(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:user-stats', args=['1611']))
        self.assertEqual(response.status_code, 200)
        results = response.data.get('results')
        self.assertEqual(results.get('changesets_in_osmcha'), 0)
        self.assertEqual(results.get('checked_changesets'), 0)
        self.assertEqual(results.get('harmful_changesets'), 0)
