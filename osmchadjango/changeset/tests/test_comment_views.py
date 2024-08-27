# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from urllib.parse import quote

from django.urls import reverse
from django.test import override_settings
from django.conf import settings

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase
from requests_oauthlib import OAuth2Session
from unittest import mock

from ...users.models import User
from ..models import Changeset
from .modelfactories import (
    ChangesetFactory, GoodChangesetFactory, HarmfulChangesetFactory
    )


class TestCommentChangesetAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap-oauth2',
            uid='123123',
            extra_data={
                'id': '123123',
                'access_token': 'bbbb'
                }
            )
        self.changeset = ChangesetFactory(id=31982802)
        self.harmful_changeset = HarmfulChangesetFactory(id=31982803)
        self.good_changeset = GoodChangesetFactory(id=31982804)

    @override_settings(ENABLE_POST_CHANGESET_COMMENTS=True)
    def test_comment_changeset_unauthenticated(self):
        comment = {'comment': 'Hello! I found an error in your edit'}
        response = self.client.post(
            reverse('changeset:comment', args=[self.harmful_changeset.id]),
            data=comment
            )

        self.assertEqual(response.status_code, 401)

    @override_settings(ENABLE_POST_CHANGESET_COMMENTS=True)
    @mock.patch.object(OAuth2Session, 'request')
    def test_comment_harmful_changeset(self, mock_oauth_client):
        # Simulate a response object
        class MockResponse():
            status_code = 200
        mock_oauth_client.return_value = MockResponse

        self.client.login(username=self.user.username, password='password')
        comment = {'comment': 'Hello! I found an error in your edit'}
        message = """Hello! I found an error in your edit
            ---
            #REVIEWED_BAD #OSMCHA
            Published using OSMCha: https://osmcha.org/changesets/31982803
            """
        response = self.client.post(
            reverse("changeset:comment", args=[self.harmful_changeset.id]),
            data=comment
            )

        self.assertEqual(response.status_code, 201)
        mock_oauth_client.assert_called_with(
            "POST",
            "{}/api/0.6/changeset/{}/comment/".format(
                settings.OSM_SERVER_URL, self.harmful_changeset.id
            ),
            headers=settings.OSM_API_USER_AGENT,
            data="text={}".format(quote(message)).encode("utf-8"),
            client_id=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_KEY,
            client_secret=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_SECRET,
        )

    @override_settings(ENABLE_POST_CHANGESET_COMMENTS=True)
    @mock.patch.object(OAuth2Session, 'request')
    def test_comment_good_changeset(self, mock_oauth_client):
        # Simulate a response object
        class MockResponse():
            status_code = 200
        mock_oauth_client.return_value = MockResponse

        self.client.login(username=self.user.username, password='password')
        comment = {'comment': 'Hello! Awesome edit! & :~) óã'}
        message = """Hello! Awesome edit! & :~) óã
            ---
            #REVIEWED_GOOD #OSMCHA
            Published using OSMCha: https://osmcha.org/changesets/31982804
            """
        response = self.client.post(
            reverse('changeset:comment', args=[self.good_changeset.id]),
            data=comment
            )

        self.assertEqual(response.status_code, 201)
        mock_oauth_client.assert_called_with(
            "POST",
            "https://www.openstreetmap.org/api/0.6/changeset/{}/comment/".format(
                self.good_changeset.id
            ),
            headers=settings.OSM_API_USER_AGENT,
            data="text={}".format(quote(message)).encode("utf-8"),
            client_id=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_KEY,
            client_secret=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_SECRET,
        )

    @override_settings(ENABLE_POST_CHANGESET_COMMENTS=True)
    @mock.patch.object(OAuth2Session, 'request')
    def test_comment_unreviewed_changeset(self, mock_oauth_client):
        """Unreviewed changeset should not receive the #OSMCHA_(GOOD or BAD)
        hashtag.
        """
        # Simulate a response object
        class MockResponse():
            status_code = 200
        mock_oauth_client.return_value = MockResponse

        self.client.login(username=self.user.username, password='password')
        comment = {'comment': 'Hello! Do you know this area?'}
        message = """Hello! Do you know this area?
            ---\n            \n            Published using OSMCha: https://osmcha.org/changesets/31982802
            """
        response = self.client.post(
            reverse('changeset:comment', args=[self.changeset.id]),
            data=comment
            )

        self.assertEqual(response.status_code, 201)
        mock_oauth_client.assert_called_with(
            "POST",
            "https://www.openstreetmap.org/api/0.6/changeset/{}/comment/".format(
                self.changeset.id
            ),
            headers=settings.OSM_API_USER_AGENT,
            data="text={}".format(quote(message)).encode("utf-8"),
            client_id=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_KEY,
            client_secret=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_SECRET,
        )

    def test_comment_good_changeset_wrong_data(self):
        self.client.login(username=self.user.username, password='password')
        comment = {'message': 'Hello! Awesome edit'}
        response = self.client.post(
            reverse('changeset:comment', args=[self.good_changeset.id]),
            data=comment
            )

        self.assertEqual(response.status_code, 400)

    def test_comment_changeset_doesnt_exist(self):
        """Request should fail if the changeset id is not on our database."""
        self.client.login(username=self.user.username, password='password')
        comment = {'message': 'Hello! Awesome edit'}
        response = self.client.post(
            reverse('changeset:comment', args=[2323]),
            data=comment
            )

        self.assertEqual(response.status_code, 404)
