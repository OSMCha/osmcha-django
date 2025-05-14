# -*- coding: utf-8 -*-
from unittest.mock import patch
from urllib.parse import quote

from django.test import TestCase
from django.conf import settings

from social_django.models import UserSocialAuth
from requests_oauthlib import OAuth2Session

from ...users.models import User
from ..models import Changeset, SuspicionReasons
from ..tasks import (
    create_changeset, format_url, get_last_replication_id, ChangesetCommentAPI
    )


class TestFormatURL(TestCase):

    def test_format_url(self):
        self.assertEqual(
            format_url(1473773),
            'https://planet.openstreetmap.org/replication/changesets/001/473/773.osm.gz'
            )


class TestCreateChangeset(TestCase):

    def test_creation(self):
        changeset = create_changeset(31450443)
        self.assertEqual(Changeset.objects.count(), 1)
        self.assertEqual(
            changeset.bbox.wkt,
            'POLYGON ((-34.9230192 -8.2197869, -34.855581 -8.2197869, -34.855581 -8.0335263, -34.9230192 -8.0335263, -34.9230192 -8.2197869))'
            )
        self.assertIsInstance(changeset.area, float)

    def test_create_changeset_without_tags(self):
        create_changeset(46755934)
        self.assertEqual(Changeset.objects.count(), 1)
        ch = Changeset.objects.get(id=46755934)
        self.assertIsNone(ch.editor)
        self.assertTrue(ch.is_suspect)
        self.assertTrue(ch.powerfull_editor)
        self.assertEqual(
            SuspicionReasons.objects.filter(
                name='Software editor was not declared'
                ).count(),
            1
            )


class TestGetLastReplicationID(TestCase):

    def test_get_last_replication_id(self):
        sequence = get_last_replication_id()
        self.assertIsNotNone(sequence)
        self.assertIsInstance(sequence, int)


class TestCreateChangesetWithoutBBOX(TestCase):

    def test_creation(self):
        changeset = create_changeset(47052680)
        self.assertEqual(Changeset.objects.count(), 1)
        self.assertTrue(changeset.bbox.empty)
        self.assertEqual(changeset.area, 0.0)


class TestChangesetCommentAPI(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider="openstreetmap-oauth2",
            uid="123123",
            extra_data={"id": "123123", "access_token": "bbbb"},
        )

    def test_changeset_comment_init(self):
        changeset_comment = ChangesetCommentAPI(self.user, 123456)
        self.assertEqual(
            changeset_comment.url,
            "https://www.openstreetmap.org/api/0.6/changeset/123456/comment/"
            )
        self.assertIsInstance(changeset_comment.client, OAuth2Session)
        self.assertEqual(changeset_comment.client.access_token, "bbbb")

    @patch.object(OAuth2Session, 'request')
    def test_post_comment(self, mock_oauth_client):
        class MockRequest():
            status_code = 200
        mock_oauth_client.return_value = MockRequest
        changeset_comment = ChangesetCommentAPI(self.user, 123456)
        changeset_comment.post_comment('Reviewed in OSMCha and set as GOOD!')

        mock_oauth_client.assert_called_with(
            "POST",
            "https://www.openstreetmap.org/api/0.6/changeset/123456/comment/",
            headers=settings.OSM_API_USER_AGENT,
            data="text={}".format(quote("Reviewed in OSMCha and set as GOOD!")).encode(
                "utf-8"
            ),
            client_id=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_KEY,
            client_secret=settings.SOCIAL_AUTH_OPENSTREETMAP_OAUTH2_SECRET,
        )
