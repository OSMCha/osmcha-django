from django.core.urlresolvers import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase
import factory
from ...users.models import User
from ...changeset.tests.modelfactories import (
    ChangesetFactory, GoodChangesetFactory, HarmfulChangesetFactory,
    SuspicionReasonsFactory, TagFactory
    )
from ..models import Priority


class TestCreatePriorityView(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='test_staff_user',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user = User.objects.create_user(
            username='test_user',
            password='password',
            email='a@b.com',
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='343234',
            )
        self.changeset = ChangesetFactory()
        self.url = reverse('priority:create')

    def test_priority_creation_unlogged(self):
        response = self.client.post(self.url, {'changeset': self.changeset.id})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Priority.objects.count(), 0)

    def test_priority_creation_normal_user(self):
        self.client.login(username=self.user, password='password')
        response = self.client.post(self.url, {'changeset': self.changeset.id})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Priority.objects.count(), 0)

    def test_priority_creation_staff_user(self):
        self.client.login(username=self.staff_user, password='password')
        response = self.client.post(self.url, {'changeset': self.changeset.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Priority.objects.count(), 1)
        self.assertEqual(Priority.objects.all()[0].changeset, self.changeset)


class PriorityFactory(factory.django.DjangoModelFactory):
    changeset = factory.SubFactory(ChangesetFactory)

    class Meta:
        model = Priority


class TestListPriorityView(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='test_staff_user',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user = User.objects.create_user(
            username='test_user',
            password='password',
            email='a@b.com',
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='343234',
            )
        self.priorities = PriorityFactory.create_batch(5)
        self.priorities_harmful_changesets = PriorityFactory.create_batch(
            5,
            changeset=factory.SubFactory(HarmfulChangesetFactory)
            )
        ChangesetFactory.create_batch(5)
        self.url = reverse('priority:list-changesets')

    def test_list_priority_unlogged(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_priority_normal_user(self):
        self.client.login(username=self.user, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_priority_staff_user(self):
        self.client.login(username=self.staff_user, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 10)

    def test_list_priority_staff_user_with_filters(self):
        self.client.login(username=self.staff_user, password='password')
        response = self.client.get(self.url, {'checked': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)


class TestPriorityDestroyAPIView(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='test_staff_user',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user = User.objects.create_user(
            username='test_user',
            password='password',
            email='a@b.com',
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='343234',
            )
        self.priority = PriorityFactory()
        self.url = reverse('priority:delete', args=[self.priority.changeset.id])

    def test_delete_priority_unlogged(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Priority.objects.count(), 1)

    def test_delete_priority_normal_user(self):
        self.client.login(username=self.user, password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Priority.objects.count(), 1)

    def test_delete_priority_staff_user(self):
        self.client.login(username=self.staff_user, password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Priority.objects.count(), 0)


class TestPriorityChangesetsStatsView(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='test_staff_user',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user = User.objects.create_user(
            username='test_user',
            password='password',
            email='a@b.com',
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='343234',
            )
        self.good_changeset = GoodChangesetFactory()
        self.harmful_changeset = HarmfulChangesetFactory()
        self.changeset = ChangesetFactory()

        self.reason_1 = SuspicionReasonsFactory(name='possible import')
        self.reason_1.changesets.add(self.good_changeset)
        self.reason_2 = SuspicionReasonsFactory(name='suspect_word')
        self.reason_2.changesets.add(self.harmful_changeset)

        self.tag_1 = TagFactory(name='Vandalism')
        self.tag_1.changesets.add(self.harmful_changeset)
        self.tag_2 = TagFactory(name='Minor errors')
        self.tag_2.changesets.add(self.good_changeset)

        PriorityFactory()
        Priority.objects.create(changeset=self.good_changeset)
        Priority.objects.create(changeset=self.harmful_changeset)

        self.url = reverse('priority:stats')

    def test_priority_stats_unlogged(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_priority_stats_normal_user(self):
        self.client.login(username=self.user, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_priority_stats_staff_user(self):
        self.client.login(username=self.staff_user, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('changesets'), 3)
        self.assertEqual(response.data.get('checked_changesets'), 2)
        self.assertEqual(response.data.get('harmful_changesets'), 1)
        self.assertEqual(len(response.data.get('reasons')), 2)
        self.assertEqual(len(response.data.get('tags')), 2)
        possible_import = {
            'name': 'possible import',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 0
            }
        self.assertIn(possible_import, response.data.get('reasons'))
        suspect_word = {
            'name': 'suspect_word',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 1
            }
        self.assertIn(suspect_word, response.data.get('reasons'))
        vandalism = {
            'name': 'Vandalism',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 1
            }
        self.assertIn(vandalism, response.data.get('tags'))
        minor_errors = {
            'name': 'Minor errors',
            'changesets': 1,
            'checked_changesets': 1,
            'harmful_changesets': 0
            }
        self.assertIn(minor_errors, response.data.get('tags'))

    def test_priority_stats_staff_user_with_filters(self):
        self.client.login(username=self.staff_user, password='password')
        response = self.client.get(self.url, {'checked': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('changesets'), 2)
        self.assertEqual(response.data.get('checked_changesets'), 2)
        self.assertEqual(response.data.get('harmful_changesets'), 1)
