from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import (Changeset, SuspicionReasons, Import, UserWhitelist,
    HarmfulReason)
from .modelfactories import ChangesetFactory, UserFactory


class TestSuspicionReasonsModel(TestCase):
    def setUp(self):
        self.reason = SuspicionReasons.objects.create(name='possible import')

    def test_creation(self):
        self.assertEqual(SuspicionReasons.objects.count(), 1)
        self.assertEqual(self.reason.__str__(), 'possible import')
        self.assertTrue(self.reason.is_visible)
        self.assertTrue(self.reason.available_to_changeset)
        self.assertTrue(self.reason.available_to_feature)
        self.reason_2 = SuspicionReasons.objects.create(
            name='Suspect word',
            description="""Changeset comment, source or imagery_used fields have
                a suspect word.""",
            is_visible=False,
            available_to_changeset=False,
            available_to_feature=True,
            )
        self.assertEqual(SuspicionReasons.objects.count(), 2)
        self.assertFalse(self.reason_2.is_visible)
        self.assertFalse(self.reason_2.available_to_changeset)
        self.assertTrue(self.reason_2.available_to_feature)

    def test_merge(self):
        self.reason_2 = SuspicionReasons.objects.create(name='possible import')
        self.assertEqual(SuspicionReasons.objects.count(), 2)
        self.changeset = ChangesetFactory()
        self.reason.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)
        self.assertEqual(self.changeset.reasons.count(), 2)
        SuspicionReasons.merge()
        self.assertEqual(SuspicionReasons.objects.count(), 1)
        self.assertEqual(self.changeset.reasons.count(), 1)


class TestHarmfulReasonModel(TestCase):
    def setUp(self):
        self.reason = HarmfulReason.objects.create(name='Illegal import')

    def test_creation(self):
        self.assertEqual(HarmfulReason.objects.count(), 1)
        self.assertEqual(self.reason.__str__(), 'Illegal import')
        self.assertTrue(self.reason.is_visible)
        self.assertTrue(self.reason.available_to_changeset)
        self.assertTrue(self.reason.available_to_feature)
        self.reason_2 = HarmfulReason.objects.create(
            name='Vandalism',
            description='The changeset is an act of vandalism.',
            is_visible=False,
            available_to_changeset=False,
            available_to_feature=True,
            )
        self.assertEqual(HarmfulReason.objects.count(), 2)
        self.assertFalse(self.reason_2.is_visible)
        self.assertFalse(self.reason_2.available_to_changeset)
        self.assertTrue(self.reason_2.available_to_feature)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            HarmfulReason.objects.create(name='Illegal import')


class TestWhitelistUserModel(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test_user')
        self.whitelist = UserWhitelist.objects.create(
            user=self.user, whitelist_user='good_user'
            )

    def test_creation(self):
        self.assertEqual(UserWhitelist.objects.count(), 1)
        self.assertEqual(
            self.whitelist.__str__(),
            'good_user whitelisted by test_user'
            )

    def test_validation(self):
        with self.assertRaises(IntegrityError):
            UserWhitelist.objects.create(
                user=self.user, whitelist_user='good_user'
                )


class TestChangesetModel(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = ChangesetFactory(id=31982803)
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)

    def test_changeset_creation(self):
        self.assertIsInstance(self.changeset, Changeset)
        self.assertEqual(Changeset.objects.all().count(), 1)
        self.assertEqual(self.changeset.reasons.all().count(), 2)
        self.assertFalse(self.changeset.checked)
        self.assertEqual(
            self.changeset.viz_tool_link(),
            'https://osmlab.github.io/changeset-map/#31982803'
            )
        self.assertEqual(
            self.changeset.osm_link(),
            'http://www.openstreetmap.org/changeset/31982803'
            )
        self.assertEqual(
            self.changeset.josm_link(),
            ('http://127.0.0.1:8111/import?url='
             'http://www.openstreetmap.org/api/0.6/changeset/31982803/download'
             )
            )
        self.assertEqual(
            self.changeset.id_link(),
            'http://www.openstreetmap.org/edit?editor=id#map=16/44.2401/-71.03477'
            )
        self.assertEqual(SuspicionReasons.objects.all().count(), 2)


class TestImportModel(TestCase):
    def setUp(self):
        self.import_1 = Import.objects.create(start=1, end=1000)
        self.import_2 = Import.objects.create(start=1001, end=2000)

    def test_import_creation(self):
        self.assertIsInstance(self.import_1, Import)
        self.assertIsInstance(self.import_1.date, datetime)
        self.assertEqual(self.import_1.__str__(), 'Import 1 - 1000')
        self.assertEqual(Import.objects.count(), 2)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            Import.objects.create(end=1000)

        with self.assertRaises(ValidationError):
            Import.objects.create(start=1000)
