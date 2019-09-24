from django.urls import reverse

from rest_framework.test import APITestCase
from social_django.models import UserSocialAuth

from ..models import User, MappingTeam
from ...changeset.tests.modelfactories import ChangesetFactory
from ...changeset.models import Changeset


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
        self.assertEqual(response.data.get('whitelists'), [])
        self.assertFalse(response.data.get('comment_feature'))
        self.assertFalse('password' in response.data.keys())

    def test_update_view(self):
        self.client.login(username='test', password='password')
        data = {
            "username": "test_user",
            "email": "admin@a.com",
            "is_staff": "true",
            "message_good": "Hello! Awesome edit!",
            "message_bad": "Hello! I found an error in your edit...",
            "comment_feature": True
            }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url)
        self.assertEqual(response.data.get('email'), 'admin@a.com')
        self.assertEqual(response.data.get('username'), 'test')
        self.assertFalse(response.data.get('is_staff'))
        self.assertEqual(
            response.data.get('message_good'),
            'Hello! Awesome edit!'
            )
        self.assertEqual(
            response.data.get('message_bad'),
            'Hello! I found an error in your edit...'
            )
        self.assertTrue(response.data.get('comment_feature'))

    def test_username_serialization(self):
        self.user.name = 'test user'
        self.user.save()
        self.client.login(username='test', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), self.user.id)
        self.assertEqual(response.data.get('username'), 'test user')

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



class TestMappingTeamListCreateAPIView(APITestCase):
    def setUp(self):
        self.url = reverse('users:mapping-team')
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
        self.payload = {
            "name": "Map Company",
            "users": [
                {
                    "username" : "test_1",
                    "doj" : "2017-02-13T00:00:00Z",
                    "uid" : "989",
                    "dol" : ""
                },
                {
                    "username" : "test_2",
                    "doj" : "2017-02-13T00:00:00Z",
                    "uid" : "987",
                    "dol" : ""
                }
            ],
            "trusted": True
        }

    def test_unauthenticated(self):
        response = self.client.post(self.url, data=self.payload)
        self.assertEqual(response.status_code, 401)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_create_authenticated(self):
        self.client.login(username='test', password='password')
        response = self.client.post(self.url, data=self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(MappingTeam.objects.count(), 1)
        self.assertEqual(MappingTeam.objects.filter(trusted=False).count(), 1)
        self.assertEqual(MappingTeam.objects.filter(trusted=True).count(), 0)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertTrue("name" in response.json().get('results')[0].keys())
        self.assertTrue("users" in response.json().get('results')[0].keys())
        self.assertTrue("trusted" in response.json().get('results')[0].keys())
        self.assertTrue("owner" in response.json().get('results')[0].keys())
        self.assertEqual(response.json().get('results')[0].get('owner'), 'test')

    def test_filters(self):
        self.client.login(username='test', password='password')
        self.client.post(self.url, data=self.payload)
        response = self.client.get(self.url, {'trusted': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(self.url, {'trusted': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(self.url, {'name': 'Map Company'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(self.url, {'name': 'Map'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(self.url, {'name': 'Other'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(self.url, {'owner': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(self.url, {'owner': 'other user'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.get(self.url, {'owner': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)


class TestMappingTeamDetailAPIView(APITestCase):
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
        self.payload = {
            "name": "Map Company",
            "users": [
                {
                    "username" : "test_1",
                    "doj" : "2017-02-13T00:00:00Z",
                    "uid" : "989",
                    "dol" : ""
                },
                {
                    "username" : "test_2",
                    "doj" : "2017-02-13T00:00:00Z",
                    "uid" : "987",
                    "dol" : ""
                }
            ],
            "trusted": True
        }
        self.team = MappingTeam.objects.create(
            name="Group of Users",
            users=self.payload,
            created_by=self.user
            )

    def test_unauthenticated(self):
        url = reverse('users:mapping-team-detail', args=[self.team.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url, data=self.payload)
        self.assertEqual(response.status_code, 401)

        response = self.client.patch(url, data=self.payload)
        self.assertEqual(response.status_code, 401)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_with_owner(self):
        url = reverse('users:mapping-team-detail', args=[self.team.id])
        self.client.login(username='test', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.put(url, data=self.payload)
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data=self.payload)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(MappingTeam.objects.filter(trusted=False).count(), 1)
        self.assertEqual(MappingTeam.objects.filter(trusted=True).count(), 0)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(MappingTeam.objects.count(), 0)

    def test_with_staff_user(self):
        user = User.objects.create_user(
            username='staff_user',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        url = reverse('users:mapping-team-detail', args=[self.team.id])
        self.client.login(username='staff_user', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.put(url, data=self.payload)
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data=self.payload)
        self.assertEqual(response.status_code, 200)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_with_other_user(self):
        user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        url = reverse('users:mapping-team-detail', args=[self.team.id])
        self.client.login(username='test_2', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.put(url, data=self.payload)
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(url, data=self.payload)
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)


class TestMappingTeamTrustingAPIView(APITestCase):
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
        self.payload = {
            "name": "Map Company",
            "users": [
                {
                    "username" : "test_1",
                    "doj" : "2017-02-13T00:00:00Z",
                    "uid" : "989",
                    "dol" : ""
                },
                {
                    "username" : "test_2",
                    "doj" : "2017-02-13T00:00:00Z",
                    "uid" : "987",
                    "dol" : ""
                }
            ],
            "trusted": True
        }
        self.team = MappingTeam.objects.create(
            name="Group of Users",
            users=self.payload,
            created_by=self.user
            )

    def test_unauthenticated(self):
        url = reverse('users:trust-mapping-team', args=[self.team.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

        url = reverse('users:untrust-mapping-team', args=[self.team.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

    def test_with_owner(self):
        url = reverse('users:trust-mapping-team', args=[self.team.id])
        self.client.login(username='test', password='password')
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)

        url = reverse('users:untrust-mapping-team', args=[self.team.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(MappingTeam.objects.filter(trusted=False).count(), 1)
        self.assertEqual(MappingTeam.objects.filter(trusted=True).count(), 0)

    def test_with_staff_user(self):
        user = User.objects.create_user(
            username='staff_user',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        url = reverse('users:trust-mapping-team', args=[self.team.id])
        self.client.login(username='staff_user', password='password')

        response = self.client.put(url)
        self.assertEqual(response.status_code, 200)
        self.team.refresh_from_db()
        self.assertEqual(MappingTeam.objects.filter(trusted=False).count(), 0)
        self.assertEqual(MappingTeam.objects.filter(trusted=True).count(), 1)

        url = reverse('users:untrust-mapping-team', args=[self.team.id])

        response = self.client.put(url)
        self.assertEqual(response.status_code, 200)
        self.team.refresh_from_db()
        self.assertEqual(MappingTeam.objects.filter(trusted=False).count(), 1)
        self.assertEqual(MappingTeam.objects.filter(trusted=True).count(), 0)

    def test_with_other_user(self):
        user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        self.client.login(username='test_2', password='password')

        url = reverse('users:trust-mapping-team', args=[self.team.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)

        url = reverse('users:untrust-mapping-team', args=[self.team.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(MappingTeam.objects.filter(trusted=False).count(), 1)
        self.assertEqual(MappingTeam.objects.filter(trusted=True).count(), 0)
        self.staff_user = User.objects.create_user(
            username='staff',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='123456',
            )


class TestUpdateDeletedUsersView(APITestCase):
    def setUp(self):
        self.url = reverse('users:update-deleted-users')
        ChangesetFactory.create_batch(50, uid="1769", user="test_user")
        ChangesetFactory.create_batch(50, uid="1234", user="old_user")
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
        self.staff_user = User.objects.create_user(
            username='staff',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.staff_user,
            provider='openstreetmap',
            uid='123456',
            )

    def test_unauthenticated(self):
        request = self.client.post(self.url, data={'uids': [1769, 1234]})
        self.assertEqual(request.status_code, 401)

    def test_non_staff_user(self):
        self.client.login(username=self.user.username, password='password')
        request = self.client.post(self.url, data={'uids': [1769, 1234]})
        self.assertEqual(request.status_code, 403)

    def test_bad_request(self):
        self.client.login(username=self.staff_user.username, password='password')
        request = self.client.post(self.url)
        self.assertEqual(request.status_code, 400)
        request = self.client.post(self.url, data={'uid': [1769, 1234]})
        self.assertEqual(request.status_code, 400)

    def test_view(self):
        user = User.objects.create_user(
            username='test_user',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='1769',
            )
        user_2 = User.objects.create_user(
            username='old_user',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=user_2,
            provider='openstreetmap',
            uid='1234',
            )
        self.client.login(username=self.staff_user.username, password='password')
        request = self.client.post(self.url, data={'uids': [1769, 1234]})
        self.assertEqual(request.status_code, 200)
        self.assertEqual(Changeset.objects.filter(uid='1769').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='user_1769').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='test_user').count(), 0)
        self.assertEqual(Changeset.objects.filter(uid='1234').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='user_1234').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='old_user').count(), 0)
        self.assertEqual(User.objects.filter(username='old_user').count(), 0)
        self.assertEqual(User.objects.filter(username='test_user').count(), 0)
        self.assertEqual(User.objects.filter(username='user_1234').count(), 1)
        self.assertEqual(User.objects.filter(username='user_1769').count(), 1)

    def test_view_as_strings(self):
        self.client.login(username=self.staff_user.username, password='password')
        request = self.client.post(self.url, data={'uids': ['1769', '1234']})
        self.assertEqual(request.status_code, 200)
        self.assertEqual(Changeset.objects.filter(uid='1769').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='user_1769').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='test_user').count(), 0)
        self.assertEqual(Changeset.objects.filter(uid='1234').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='user_1234').count(), 50)
        self.assertEqual(Changeset.objects.filter(user='old_user').count(), 0)
