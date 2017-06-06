from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO
from django.utils import timezone

from ...feature.tests.modelfactories import FeatureFactory, CheckedFeatureFactory
from ...feature.models import Feature
from ..models import Changeset
from .modelfactories import ChangesetFactory, GoodChangesetFactory


class TestImportReplicationFile(TestCase):
    def setUp(self):
        self.filename = settings.APPS_DIR.path(
            'changeset/tests/test_fixtures/011.osm.gz'
            )
        self.out = StringIO()
        call_command('import_file', self.filename, stdout=self.out)

    def test_import(self):
        self.assertEqual(Changeset.objects.count(), 7)
        self.assertIn(
            '7 changesets created from {}.'.format(self.filename),
            self.out.getvalue()
            )


class TestDeleteOldData(TestCase):
    def setUp(self):
        self.six_months_ago = timezone.now() - timedelta(days=180)
        ChangesetFactory.create_batch(10, date=self.six_months_ago)

        # a changeset and a feature that should be deleted
        self.old_changeset_1 = ChangesetFactory(date=self.six_months_ago)
        self.feature = FeatureFactory(changeset=self.old_changeset_1)

        # a feature that shouldn't be deleted, so the changeset shouldn't too
        self.old_changeset_2 = ChangesetFactory(date=self.six_months_ago)
        self.checked_feature = CheckedFeatureFactory(changeset=self.old_changeset_2)

        # a changeset that shouldn't be deleted, so the feature shouldn't too
        self.old_checked_changeset = GoodChangesetFactory(date=self.six_months_ago)
        self.old_feature_of_old_checked_changeset = FeatureFactory(
            changeset=self.old_checked_changeset
            )
        # two changesets that shouldn't be deleted
        self.changeset = ChangesetFactory()
        self.checked_changeset = GoodChangesetFactory()
        call_command('delete_old_data')

    def test_command(self):
        self.assertEqual(Changeset.objects.count(), 4)
        self.assertEqual(Feature.objects.count(), 2)
        self.assertEqual(
            Feature.objects.filter(
                changeset__date__lt=(timezone.now() - timedelta(days=180)),
                changeset__checked=False,
                checked=False
                ).count(),
            0
            )
        self.assertEqual(
            Changeset.objects.filter(
                date__lt=(timezone.now() - timedelta(days=180)),
                checked=False,
                features=None
                ).count(),
            0
            )

        self.assertIn(self.changeset, Changeset.objects.all())
        self.assertIn(self.old_checked_changeset, Changeset.objects.all())
        self.assertIn(self.checked_changeset, Changeset.objects.all())
        self.assertIn(self.old_changeset_2, Changeset.objects.all())
