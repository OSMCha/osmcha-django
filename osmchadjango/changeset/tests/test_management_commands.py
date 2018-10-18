from datetime import timedelta, datetime, date
import json

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO
from django.utils import timezone

from ..models import Changeset, SuspicionReasons
from .modelfactories import (
    ChangesetFactory, GoodChangesetFactory, SuspectChangesetFactory,
    FeatureFactory
    )


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

        # a changeset that should be deleted
        self.old_changeset_1 = ChangesetFactory(date=self.six_months_ago)
        # a changeset that shouldn't be deleted
        self.old_checked_changeset = GoodChangesetFactory(date=self.six_months_ago)
        # two changesets that shouldn't be deleted
        self.changeset = ChangesetFactory()
        self.checked_changeset = GoodChangesetFactory()
        call_command('delete_old_data')

    def test_command(self):
        self.assertEqual(Changeset.objects.count(), 3)
        self.assertEqual(
            Changeset.objects.filter(
                date__lt=(timezone.now() - timedelta(days=180)),
                checked=False,
                ).count(),
            0
            )

        self.assertIn(self.changeset, Changeset.objects.all())
        self.assertIn(self.old_checked_changeset, Changeset.objects.all())
        self.assertIn(self.checked_changeset, Changeset.objects.all())


class TestMergeReasons(TestCase):
    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='New mapper')
        self.reason_2 = SuspicionReasons.objects.create(
            name='New mapper <5 mapping days'
            )
        self.changesets = SuspectChangesetFactory.create_batch(10)
        for c in self.changesets:
            self.reason_2.changesets.add(c)

        self.reason_1.changesets.add(self.changesets[0])

    def test_merge(self):
        call_command('merge_reasons', self.reason_2.id, self.reason_1.id)
        self.assertEqual(SuspicionReasons.objects.count(), 1)
        self.assertEqual(
            SuspicionReasons.objects.filter(name='New mapper').count(), 1
            )
        self.assertEqual(
            SuspicionReasons.objects.filter(
                name='New mapper <5 mapping days'
                ).count(),
            0
            )
        self.assertEqual(
            Changeset.objects.filter(reasons__name='New mapper').count(),
            10
            )
        self.assertEqual(
            Changeset.objects.filter(
                reasons__name='New mapper <5 mapping days'
                ).count(),
            0
            )

    def test_error(self):
        self.out = StringIO()
        call_command(
            'merge_reasons',
            self.reason_2.id + 1,
            self.reason_1.id,
            stdout=self.out
            )
        self.assertIn('Verify the SuspicionReasons ids.', self.out.getvalue())
        self.assertIn('One or both of them does not exist.', self.out.getvalue())


class TestMigrateFeatures(TestCase):
    def setUp(self):
        self.changeset = ChangesetFactory(id=31982803, date=date(2018, 1, 1))
        self.changeset_2 = ChangesetFactory(id=31982804)
        self.features_1 = FeatureFactory.create_batch(
            10,
            changeset=self.changeset
            )
        self.features_2 = FeatureFactory.create_batch(
            5,
            changeset=self.changeset_2
            )
        self.reason = SuspicionReasons.objects.create(
            name='new mapper edits'
            )
        self.reason_2 = SuspicionReasons.objects.create(
            name='Vandalism'
            )
        for feature in self.features_1:
            self.reason.features.add(feature)
            self.reason_2.features.add(feature)

    def test_migration(self):
        call_command(
            'migrate_features',
            '2018-01-01',
            (date.today() + timedelta(days=1)).isoformat()
            )
        self.changeset.refresh_from_db()
        self.changeset_2.refresh_from_db()
        self.assertEqual(len(self.changeset.new_features), 10)
        self.assertEqual(len(self.changeset_2.new_features), 5)
        self.assertEqual(
            self.changeset.new_features[0].get('reasons'),
            [self.reason.id, self.reason_2.id]
            )
        self.assertIsNotNone(self.changeset.new_features[0].get('osm_id'))
        self.assertIn('node-', self.changeset.new_features[0].get('url'))
        self.assertEqual(self.changeset.new_features[0].get('version'), 1)
        self.assertEqual(self.changeset.new_features[0].get('name'), 'Test')
        self.assertEqual(
            self.changeset.new_features[0].get('primary_tags'),
            {'building': 'yes'}
            )
        self.assertIsNotNone(self.changeset.new_features[0].get('reasons'))

    def test_partial_migration(self):
        call_command(
            'migrate_features',
            '2018-01-02',
            (date.today() + timedelta(days=1)).isoformat()
            )
        self.changeset.refresh_from_db()
        self.changeset_2.refresh_from_db()
        self.assertEqual(len(self.changeset.new_features), 0)
        self.assertEqual(len(self.changeset_2.new_features), 5)

    def test_feature_without_properties(self):
        self.changeset.features.all()[0].geojson = json.dumps({'id': 1232})
        self.changeset.features.all()[0].save()
        call_command(
            'migrate_features',
            '2018-01-01',
            (date.today() + timedelta(days=1)).isoformat()
            )
        self.changeset.refresh_from_db()
        self.changeset_2.refresh_from_db()
        self.assertEqual(len(self.changeset.new_features), 10)
        self.assertEqual(
            self.changeset.new_features[0].get('reasons'),
            [self.reason.id, self.reason_2.id]
            )
        self.assertIsNotNone(self.changeset.new_features[0].get('osm_id'))
        self.assertIn('node-', self.changeset.new_features[0].get('url'))
        self.assertEqual(self.changeset.new_features[0].get('version'), 1)
