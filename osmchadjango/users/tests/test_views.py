from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from ..models import User


class TestUserDetailAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
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
