from django.core.urlresolvers import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ..models import SuspicionReasons, Tag


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
        self.assertEqual(len(response.data), 1)
        reason_dict = {
            'id': self.reason_1.id,
            'name': 'possible import',
            'description': self.reason_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(reason_dict, response.data)

    def test_admin_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


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
        self.assertEqual(len(response.data), 1)
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
            response.data
            )

    def test_admin_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:tags-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
