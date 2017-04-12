from django.test import TestCase
from django.core.management import call_command

from social_django.models import UserSocialAuth

from ..models import User


class TestUpdateUserNameCommand(TestCase):
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

    def test_command(self):
        call_command('update_user_names')
        self.user.refresh_from_db()
        self.user_2.refresh_from_db()
        self.assertEqual(self.user.name, 'Wille Marcel')
        self.assertEqual(self.user_2.name, u'Narcélio de Sá')
