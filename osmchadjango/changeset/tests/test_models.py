from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import (
    Changeset, SuspicionReasons, Import, UserWhitelist, Tag
    )
from .modelfactories import ChangesetFactory, UserFactory


class TestSuspicionReasonsModel(TestCase):
    def setUp(self):
        self.reason = SuspicionReasons.objects.create(name='possible import')

    def test_creation(self):
        self.assertEqual(SuspicionReasons.objects.count(), 1)
        self.assertEqual(self.reason.__str__(), 'possible import')
        self.assertTrue(self.reason.is_visible)
        self.assertTrue(self.reason.for_changeset)
        self.assertTrue(self.reason.for_feature)
        self.reason_2 = SuspicionReasons.objects.create(
            name='Suspect word',
            description="""Changeset comment, source or imagery_used fields have
                a suspect word.""",
            is_visible=False,
            for_changeset=False,
            for_feature=True,
            )
        self.assertEqual(SuspicionReasons.objects.count(), 2)
        self.assertFalse(self.reason_2.is_visible)
        self.assertFalse(self.reason_2.for_changeset)
        self.assertTrue(self.reason_2.for_feature)

    def test_unique(self):
        with self.assertRaises(ValidationError):
            SuspicionReasons.objects.create(name='possible import')


class TestTagModel(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name='Illegal import')

    def test_creation(self):
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(self.tag.__str__(), 'Illegal import')
        self.assertTrue(self.tag.is_visible)
        self.assertTrue(self.tag.for_changeset)
        self.assertTrue(self.tag.for_feature)
        self.tag_2 = Tag.objects.create(
            name='Vandalism',
            description='The changeset is an act of vandalism.',
            is_visible=False,
            for_changeset=False,
            for_feature=True,
            )
        self.assertEqual(Tag.objects.count(), 2)
        self.assertFalse(self.tag_2.is_visible)
        self.assertFalse(self.tag_2.for_changeset)
        self.assertTrue(self.tag_2.for_feature)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            Tag.objects.create(name='Illegal import')


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
        self.changeset = ChangesetFactory(id=31982803)

    def test_changeset_creation(self):
        self.assertIsInstance(self.changeset, Changeset)
        self.assertGreater(self.changeset.area, 0)
        self.assertEqual(Changeset.objects.all().count(), 1)

        self.assertFalse(self.changeset.checked)
        self.assertEqual(self.changeset.comments_count, 1)
        self.assertEqual(
            self.changeset.viz_tool_link(),
            'https://osmlab.github.io/changeset-map/#31982803'
            )
        self.assertEqual(
            self.changeset.osm_link(),
            'https://www.openstreetmap.org/changeset/31982803'
            )
        self.assertEqual(
            self.changeset.josm_link(),
            ('http://127.0.0.1:8111/import?url='
             'https://www.openstreetmap.org/api/0.6/changeset/31982803/download'
             )
            )
        self.assertEqual(
            self.changeset.id_link(),
            'https://www.openstreetmap.org/edit?editor=id#map=16/44.2401/-71.03477'
            )

    def test_suspicion_reasons(self):
        reason_1 = SuspicionReasons.objects.create(name='possible import')
        reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        reason_1.changesets.add(self.changeset)
        reason_2.changesets.add(self.changeset)
        self.assertEqual(self.changeset.reasons.all().count(), 2)

    def test_tag(self):
        tag = Tag.objects.create(name='Illegal import')
        tag_2 = Tag.objects.create(name='Vandalism')
        tag.changesets.add(self.changeset)
        tag_2.changesets.add(self.changeset)
        self.assertEqual(self.changeset.tags.all().count(), 2)

    def test_empty_new_feature_field(self):
        self.assertEqual(self.changeset.new_features, [])

    def test_new_feature_field(self):
        json_content = [
            {"osm_id": 123, "url": "node-123", "reasons": [1, 2], },
            {"osm_id": 321, "url": "way-321", "reasons": [13], 'note': 'Test'}
        ]
        changeset = ChangesetFactory(
            id=31982804,
            new_features=json_content
            )
        self.assertEqual(Changeset.objects.all().count(), 2)
        self.assertEqual(changeset.new_features, json_content)

    def test_metadata_field(self):
        self.assertEqual(
            self.changeset.metadata,
            {'changesets_count': 99, 'host': 'https://ideditor.netlify.app'}
            )


class TestChangesetModelOrdering(TestCase):
    def setUp(self):
        ChangesetFactory.create_batch(10)
        self.last_id = Changeset.objects.all()[0].id
        self.first_id = self.last_id - Changeset.objects.count()

    def test_changeset_ordering(self):
        self.assertEqual(
            [i.id for i in Changeset.objects.all()],
            list(range(self.last_id, self.first_id, -1))
            )


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
