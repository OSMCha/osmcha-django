from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase, TransactionTestCase

from ..models import User, MappingTeam


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


class TestMappingTeamModel(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        self.team = MappingTeam.objects.create(
            name="Group of Users",
            users=[],
            created_by=self.user
        )
        self.team_2 = MappingTeam.objects.create(
            name="Map Company",
            trusted=True,
            created_by=self.user,
            users=[
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
        )

    def test_creation(self):
        self.assertEqual(MappingTeam.objects.count(), 2)
        self.assertEqual(self.team.trusted, False)
        self.assertEqual(self.team.users, [])
        self.assertEqual(self.team.name, "Group of Users")
        self.assertEqual(self.team.created_by, self.user)
        self.assertIsNotNone(self.team.date)

        self.assertEqual(self.team_2.trusted, True)
        self.assertEqual(
            self.team_2.users,
            [
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
            ]
            )
        self.assertEqual(self.team_2.name, "Map Company")
        self.assertEqual(self.team_2.__str__(), "Map Company by test")

    def test_unique_name_validation(self):
        self.user_2 = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        with self.assertRaises(IntegrityError):
            MappingTeam.objects.create(
                name="Group of Users",
                users=[],
                created_by=self.user_2
                )

        self.assertEqual(MappingTeam.objects.count(), 2)

        with self.assertRaises(IntegrityError):
            MappingTeam.objects.create(
                name="Group of Users",
                users=[],
                created_by=self.user
                )

        with self.assertRaises(IntegrityError):
            MappingTeam.objects.create(
                name="Map Company",
                trusted=True,
                created_by=self.user_2
                )
