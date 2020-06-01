from django.urls import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ...changeset.tests.modelfactories import SuspicionReasonsFactory
from ..models import ChallengeIntegration


class TestChallengeIntegrationListCreateView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user_1',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user_2 = User.objects.create_user(
            username='test_2',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='444444',
            )
        self.reason_1 = SuspicionReasonsFactory(name="Grafitti")
        self.url = reverse('challenge:list-create')

    def test_list_challenges_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_list_challenges_non_staff_user(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_challenge_unauthenticated(self):
        response = self.client.post(self.url, {'challenge_id': 1234, 'reasons': [self.reason_1.id]})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(ChallengeIntegration.objects.count(), 0)

    def test_create_challenge_non_staff_user(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.post(self.url, {'challenge_id': 1234, 'reasons': [self.reason_1.id]})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ChallengeIntegration.objects.count(), 0)

    def test_create_and_list_challenges_staf_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, {'challenge_id': 1234, 'reasons': [self.reason_1.id]})
        self.assertEqual(response.status_code, 201)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertEqual(response.data.get('results')[0].get('reasons'), [self.reason_1.id])
        self.assertTrue(response.data.get('results')[0].get('active'))


class TestChallengeIntegrationDetailView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user_1',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.user_2 = User.objects.create_user(
            username='test_2',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='444444',
            )
        self.reason_1 = SuspicionReasonsFactory(name="Grafitti")
        self.reason_2 = SuspicionReasonsFactory(name="Vandalism")
        self.integration = ChallengeIntegration.objects.create(challenge_id=1234, user=self.user)
        self.integration.reasons.add(self.reason_1)

    def test_get_challenges_unauthenticated(self):
        response = self.client.get(
            reverse('challenge:detail', args=[self.integration.pk])
            )
        self.assertEqual(response.status_code, 401)

    def test_list_challenges_non_staff_user(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.get(
            reverse('challenge:detail', args=[self.integration.pk])
            )
        self.assertEqual(response.status_code, 403)

    def test_delete_challenge_unauthenticated(self):
        response = self.client.delete(
            reverse('challenge:detail', args=[self.integration.pk])
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(ChallengeIntegration.objects.count(), 1)

    def test_delete_challenge_non_staff_user(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.delete(
            reverse('challenge:detail', args=[self.integration.pk])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ChallengeIntegration.objects.count(), 1)

    def test_delete_challenge_staff_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(
            reverse('challenge:detail', args=[self.integration.pk])
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(ChallengeIntegration.objects.count(), 0)

    def test_update_challenge_unauthenticated(self):
        response = self.client.put(
            reverse('challenge:detail', args=[self.integration.pk]),
            {'challenge_id': 12345, 'reasons': [self.reason_1.id]}
            )
        self.assertEqual(response.status_code, 401)

        response = self.client.patch(
            reverse('challenge:detail', args=[self.integration.pk]),
            {'challenge_id': 12345, 'reasons': [self.reason_1.id]}
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            ChallengeIntegration.objects.filter(challenge_id=12345).count(),
            0
            )

    def test_update_challenge_non_staff_user(self):
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.put(
            reverse('challenge:detail', args=[self.integration.pk]),
            {'challenge_id': 12345, 'reasons': [self.reason_1.id]}
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            ChallengeIntegration.objects.filter(challenge_id=12345).count(),
            0
            )

        response = self.client.patch(
            reverse('challenge:detail', args=[self.integration.pk]),
            {'challenge_id': 12345, 'reasons': [self.reason_1.id]}
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            ChallengeIntegration.objects.filter(challenge_id=12345).count(),
            0
            )

    def test_update_challenge_staff_user_put_method(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('challenge:detail', args=[self.integration.pk]),
            {'challenge_id': 12345, 'reasons': [self.reason_1.id]}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ChallengeIntegration.objects.filter(challenge_id=12345).count(),
            1
            )
        self.assertEqual(
            ChallengeIntegration.objects.filter(challenge_id=1234).count(),
            0
            )

    def test_update_challenge_staff_user_patch_method(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.patch(
            reverse('challenge:detail', args=[self.integration.pk]),
            {'challenge_id': 123456, 'reasons': [self.reason_1.id, self.reason_2.id]}
            )
        self.assertEqual(response.status_code, 200)
        self.integration.refresh_from_db()
        self.assertEqual(self.integration.challenge_id, 123456)
        self.assertEqual(self.integration.reasons.count(), 2)
        self.assertEqual(
            ChallengeIntegration.objects.filter(challenge_id=1234).count(),
            0
            )
