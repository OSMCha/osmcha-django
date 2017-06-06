from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase
from social_django.models import UserSocialAuth

from ..models import User


class TestCurrentUserDetailAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        self.social_auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.social_auth.set_extra_data({'avatar': 'http://theurl.org/pic.jpg'})
        self.url = reverse('users:detail')

    def test_view_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_view(self):
        self.client.login(username='test', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), self.user.id)
        self.assertEqual(response.data.get('username'), 'test')
        self.assertEqual(response.data.get('email'), 'a@a.com')
        self.assertEqual(response.data.get('uid'), '123123')
        self.assertEqual(response.data.get('is_staff'), False)
        self.assertEqual(response.data.get('is_active'), True)
        self.assertEqual(response.data.get('avatar'), 'http://theurl.org/pic.jpg')
        self.assertFalse('password' in response.data.keys())

    def test_update_view(self):
        self.client.login(username='test', password='password')
        data = {
            "username": "test_user",
            "email": "admin@a.com",
            "is_staff": "true"
            }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url)
        self.assertEqual(response.data.get('email'), 'admin@a.com')
        self.assertEqual(response.data.get('username'), 'test')
        self.assertEqual(response.data.get('is_staff'), False)

    def test_uid_field_of_non_social_user(self):
        self.user_2 = User.objects.create_user(
            username='test_2',
            password='password',
            email='b@a.com'
            )
        self.client.login(username='test_2', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.data.get('uid'), None)
        self.assertEqual(response.data.get('avatar'), None)


class TestSocialAuthAPIView(APITestCase):
    def setUp(self):
        self.url = reverse('users:social-auth')

    def test_get_response(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_receive_oauth_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('oauth_token', response.data.keys())
        self.assertIn('oauth_token_secret', response.data.keys())
