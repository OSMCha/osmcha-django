from django.urls import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ..models import UserWhitelist


class TestWhitelistUserView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user_2 = User.objects.create_user(
            username='test_user',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='444444',
            )
        self.url = reverse('changeset:whitelist-user')

    def test_list_whitelist_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_create_whitelist_unauthenticated(self):
        response = self.client.post(self.url, {'whitelist_user': 'good_user'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(UserWhitelist.objects.count(), 0)

    def test_create_and_list_whitelist(self):
        # test whitelisting a user and getting the list of whitelisted users
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, {'whitelist_user': 'good_user'})
        self.assertEqual(response.status_code, 201)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)
        self.client.logout()
        # the same with another user
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.post(self.url, {'whitelist_user': 'the_user'})
        self.assertEqual(response.status_code, 201)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)

        self.assertEqual(UserWhitelist.objects.count(), 2)
        self.assertEqual(UserWhitelist.objects.filter(user=self.user).count(), 1)
        self.assertEqual(UserWhitelist.objects.filter(user=self.user_2).count(), 1)
        self.assertEqual(
            UserWhitelist.objects.filter(whitelist_user='good_user').count(), 1
            )
        self.assertEqual(
            UserWhitelist.objects.filter(whitelist_user='the_user').count(), 1
            )

    def test_whitelist_same_user_two_times(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, {'whitelist_user': 'good_user'})
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.url, {'whitelist_user': 'good_user'})
        self.assertEqual(response.status_code, 403)


class TestUserWhitelistDestroyAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        UserWhitelist.objects.create(user=self.user, whitelist_user='good_user')
        UserWhitelist.objects.create(user=self.user, whitelist_user='good user#23 %7á')
        self.user_2 = User.objects.create_user(
            username='test_user',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='444444',
            )
        UserWhitelist.objects.create(user=self.user_2, whitelist_user='the_user')

    def test_delete_whitelist_unauthenticated(self):
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['good_user'])
            )
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['the_user'])
            )
        self.assertEqual(response.status_code, 401)

    def test_delete_userwhitelist(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['good_user'])
            )
        self.assertEqual(response.status_code, 204)
        # test username with blankspaces and special chars
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['good user#23 %7á'])
            )
        self.assertEqual(response.status_code, 204)
        # test delete a whitelist of another user
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['the_user'])
            )
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        self.client.login(username=self.user_2.username, password='password')
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['the_user'])
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(UserWhitelist.objects.count(), 0)
