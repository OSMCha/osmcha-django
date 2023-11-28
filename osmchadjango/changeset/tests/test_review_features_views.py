# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from urllib.parse import quote

from django.urls import reverse
from django.test import override_settings

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase
from requests_oauthlib import OAuth1Session
from unittest import mock

from ...users.models import User
from ..models import Changeset
from .modelfactories import ChangesetFactory


class TestReviewFeaturesAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='345',
            extra_data={
                'id': '345',
                'access_token': {
                    'oauth_token': 'aaaa',
                    'oauth_token_secret': 'bbbb'
                    }
                }
            )
        self.changeset = ChangesetFactory(id=31982802)

    def test_review_feature_unauthenticated(self):
        response = self.client.put(
            reverse(
                'changeset:review-harmful-feature',
                args=[self.changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 401)

    def test_remove_review_feature_unauthenticated(self):
        response = self.client.delete(
            reverse(
                'changeset:review-harmful-feature',
                args=[self.changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 401)

    def test_remove_review_feature(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(
            reverse(
                'changeset:review-harmful-feature',
                args=[self.changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 400)
        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.reviewed_features, [])
        # now add a feature to the changeset
        response = self.client.put(
            reverse(
                'changeset:review-harmful-feature',
                args=[self.changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 200)
        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.reviewed_features, [{"id": "node-1234", "user": "test_2"}])
        # and remove the feature should work
        response = self.client.delete(
            reverse(
                'changeset:review-harmful-feature',
                args=[self.changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 200)
        self.changeset.refresh_from_db()
        self.assertEqual(self.changeset.reviewed_features, [])

    def test_review_feature_own_changeset(self):
        changeset = ChangesetFactory(id=457890, uid="345", user="test_2")
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse(
                'changeset:review-harmful-feature',
                args=[changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 403)

    def test_remove_review_feature_own_changeset(self):
        changeset = ChangesetFactory(
            id=457890,
            uid="345",
            user="test_2",
            reviewed_features=[{"id": "node-1234", "user": "test"}]
            )
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(
            reverse(
                'changeset:review-harmful-feature',
                args=[changeset.id, "node", 1234]
                )
            )
        self.assertEqual(response.status_code, 403)
