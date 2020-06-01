from datetime import datetime

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import ChallengeIntegration

from ...changeset.tests.modelfactories import SuspicionReasonsFactory, UserFactory


class TestMapRouletteChallengeModel(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test_user')
        reason_1 = SuspicionReasonsFactory(name="Grafitti")
        self.integration = ChallengeIntegration.objects.create(challenge_id=1234, user=self.user)
        self.integration.reasons.add(reason_1)

    def test_challenge_creation(self):
        self.assertIsInstance(self.integration, ChallengeIntegration)
        self.assertEqual(self.integration.challenge_id, 1234)
        self.assertTrue(self.integration.active)
        self.assertIsNotNone(self.integration.created)
        self.assertIsInstance(self.integration.created, datetime)
        self.assertIsNotNone(self.integration.user)
        self.assertIsInstance(self.integration.user, get_user_model())
        self.assertEqual(self.integration.__str__(), 'Challenge 1234')

    def test_required_user_field(self):
        with self.assertRaises(IntegrityError):
            ChallengeIntegration.objects.create(challenge_id=1234)

    def test_required_challenge_id_field(self):
        with self.assertRaises(IntegrityError):
            ChallengeIntegration.objects.create(user=self.user)
