from django.urls import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from .modelfactories import ChangesetFactory


class TestSetChangesetTagChanges(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap-oauth2',
            uid='123123',
            )

        self.changeset = ChangesetFactory()
        self.valid_payload = {
            "surface": ["paved", "unpaved", "asphalt", "grass"],
            "lanes": ["1", "2"],
            "height": ["1.5"]
            }

    def test_unathenticated_request(self):
        """Unauthenticated users can not access these endpoints."""
        # test remove from changesets
        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data=self.valid_payload
            )
        self.assertEqual(response.status_code, 401)
        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.tag_changes, {})

    def test_normal_user_request(self):
        """Only staff users can use these endpoints."""
        user = User.objects.create_user(
            username='test_3',
            password='password',
            email='a@a.com',
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap-oauth2',
            uid='99989',
            )
        self.client.login(username=user.username, password='password')

        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data=self.valid_payload
            )
        self.assertEqual(response.status_code, 403)
        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.tag_changes, {})

    def test_staff_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data=self.valid_payload
            )
        self.assertEqual(response.status_code, 200)
        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.tag_changes, self.valid_payload)

    def test_invalid_payloads(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data=["paved", "unpaved"]
            )
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data={"highway": {"new": "paved", "old": "unpaved"}}
            )
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data={
                "surface": ["paved", "unpaved", "asphalt", "grass"],
                "highway": [{"newValue": "tertiary"}]
                }
            )
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse('changeset:set-tag-changes', args=[self.changeset.id]),
            data={
                "lanes": [2, 4, 1],
                }
            )
        self.assertEqual(response.status_code, 400)

        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.tag_changes, {})
