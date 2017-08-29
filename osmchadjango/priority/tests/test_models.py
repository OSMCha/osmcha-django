from django.test import TestCase
from django.db.utils import IntegrityError

from ..models import Priority
from osmchadjango.changeset.tests.modelfactories import ChangesetFactory


class TestPriorityModel(TestCase):
    def setUp(self):
        self.changeset = ChangesetFactory()
        self.priority = Priority.objects.create(changeset=self.changeset)

    def test_creation(self):
        self.assertEqual(Priority.objects.count(), 1)
        self.assertEqual(
            self.priority.__str__(),
            'Changeset {}'.format(self.changeset.id)
            )

    def test_validation(self):
        with self.assertRaises(IntegrityError):
            Priority.objects.create(changeset=self.changeset)
