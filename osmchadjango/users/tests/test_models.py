from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import User


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        self.user_complete = User.objects.create_user(
            username='test_complete_user',
            password='password',
            email='a@a.com',
            message_good='Hello! Thank you for this amazing changeset!',
            message_bad='Hello! I found some errors in your changeset...',
            comment_feature=True
            )

    def test_basic_user_model(self):
        self.assertIsInstance(self.user, User)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.user.username, 'test')
        self.assertEqual(self.user.email, 'a@a.com')
        self.assertFalse(self.user.comment_feature)
        self.assertEqual(
            self.user_complete.message_good,
            'Hello! Thank you for this amazing changeset!'
            )
        self.assertEqual(
            self.user_complete.message_bad,
            'Hello! I found some errors in your changeset...'
            )
        self.assertTrue(self.user_complete.comment_feature)
