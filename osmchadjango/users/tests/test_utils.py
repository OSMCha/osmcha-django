# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from social_django.models import UserSocialAuth

from ..models import User
from ..utils import update_user_name


class TestUpdateUserName(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='WilleMarcel',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='5654409',
            )
        self.user_2 = User.objects.create_user(
            username='NarcéliodeSá',
            email='c@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='612405',
            )

    def test_update_user_name(self):
        update_user_name(self.user)
        update_user_name(self.user_2)
        self.assertEqual(self.user.name, 'Wille Marcel')
        self.assertEqual(self.user_2.name, 'narceliodesa')

    def test_user_with_wrong_uid(self):
        user = User.objects.create_user(
            username='test',
            email='d@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='1989776798',
            )
        update_user_name(user)
        self.assertEqual(user.name, '')

    def test_user_without_social_auth(self):
        user = User.objects.create_user(
            username='test',
            email='d@a.com',
            password='password'
            )
        update_user_name(user)
        self.assertEqual(user.name, '')
