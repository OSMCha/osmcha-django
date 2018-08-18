from django.urls import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ..models import SuspicionReasons, Tag
from .modelfactories import ChangesetFactory


class TestSuspicionReasonsAPIListView(APITestCase):
    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(
            name='possible import',
            description='A changeset that created too much map elements.'
            )
        self.reason_2 = SuspicionReasons.objects.create(
            name='suspect word',
            is_visible=False
            )
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

    def test_view(self):
        response = self.client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)
        reason_dict = {
            'id': self.reason_1.id,
            'name': 'possible import',
            'description': self.reason_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(reason_dict, response.data.get('results'))

    def test_admin_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 2)


class TestTagAPIListView(APITestCase):
    def setUp(self):
        self.tag_1 = Tag.objects.create(
            name='Illegal import',
            description='A changeset that imported illegal data.'
            )
        self.tag_2 = Tag.objects.create(
            name='Vandalism in my city',
            is_visible=False
            )
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

    def test_view(self):
        response = self.client.get(reverse('changeset:tags-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)
        tag_dict = {
            'id': self.tag_1.id,
            'name': 'Illegal import',
            'description': self.tag_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(
            tag_dict,
            response.data.get('results')
            )

    def test_admin_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:tags-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 2)


class TestBatchAddSuspicionReasons(APITestCase):
    def setUp(self):
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
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='mass modification')
        self.changesets = ChangesetFactory.create_batch(4)

    def test_unathenticated_request(self):
        """Unauthenticated users can not access these endpoints."""
        # test add reason_1 to changesets
        response = self.client.post(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"changesets": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.reason_1.changesets.count(), 0)

    def test_normal_user_request(self):
        """Only staff users can use these endpoints."""
        user = User.objects.create_user(
            username='test_3',
            password='password',
            email='a@a.com',
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='99989',
            )
        self.client.login(username=user.username, password='password')
        response = self.client.post(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"changesets": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 403)

    def test_staff_user_request(self):
        self.client.login(username=self.user.username, password='password')
        # test add reason_1 to changesets
        response = self.client.post(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"changesets": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.reason_1.changesets.count(), 4)

    def test_bad_request(self):
        self.client.login(username=self.user.username, password='password')
        # test add reason_1 to changesets
        response = self.client.post(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"features": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 400)


class TestBatchRemoveSuspicionReasons(APITestCase):
    def setUp(self):
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
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='mass modification')

        self.changeset_1 = ChangesetFactory()
        self.changeset_2 = ChangesetFactory()
        self.changesets = [self.changeset_1, self.changeset_2]
        self.reason_1.changesets.add(self.changeset_1)
        self.reason_1.changesets.add(self.changeset_2)

    def test_unathenticated_request(self):
        """Unauthenticated users can not access these endpoints."""
        # test remove from changesets
        response = self.client.delete(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"changesets": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.reason_1.changesets.count(), 2)

    def test_normal_user_request(self):
        """Only staff users can use these endpoints."""
        user = User.objects.create_user(
            username='test_3',
            password='password',
            email='a@a.com',
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='99989',
            )
        self.client.login(username=user.username, password='password')

        # test remove from the changesets
        response = self.client.delete(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"changesets": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.reason_1.changesets.count(), 2)

    def test_staff_user_request_remove_from_changeset(self):
        self.client.login(username=self.user.username, password='password')
        # test remove reason from changesets
        response = self.client.delete(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"changesets": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.reason_1.changesets.count(), 0)

    def test_bad_request(self):
        self.client.login(username=self.user.username, password='password')
        # test remove from the changesets
        response = self.client.delete(
            reverse('changeset:changeset-reasons', args=[self.reason_1.id]),
            data={"features": [c.id for c in self.changesets]}
            )
        self.assertEqual(response.status_code, 400)
