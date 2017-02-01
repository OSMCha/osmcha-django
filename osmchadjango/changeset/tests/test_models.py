from datetime import datetime

from django.test import TestCase
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from osmcha.changeset import Analyse

from ..models import Changeset, SuspicionReasons, Import


class TestChangesetModel(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = Changeset.objects.create(
            id=31982803,
            uid='123123',
            user='test',
            editor='Potlatch 2',
            powerfull_editor=False,
            date=datetime.now(),
            create=2000,
            modify=10,
            delete=30,
            is_suspect=True,
            bbox=Polygon([
                (-71.0646843, 44.2371354), (-71.0048652, 44.2371354),
                (-71.0048652, 44.2430624), (-71.0646843, 44.2430624),
                (-71.0646843, 44.2371354)
                ])
            )
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
        self.assertEqual(SuspicionReasons.objects.all().count(), 2)

    def test_save_user_details(self):
        analyze = Analyse(31450443)  # A random changeset
        analyze.full_analysis()

        # Removing these values from the object
        analyze_dict = analyze.__dict__.copy()
        for key in analyze.__dict__:
            if analyze.__dict__.get(key) == '':
                analyze_dict.pop(key)
        analyze_dict.pop('suspicion_reasons')
        analyze_dict.pop('user_details')

        changeset = Changeset.objects.create(**analyze_dict)
        changeset.save()

        self.assertIsNone(changeset.user_detail)
        changeset.save_user_details(analyze)
        self.assertIsNotNone(changeset.user_detail)

        self.assertEqual(changeset.user_detail.contributor_name, 'Tobsen Laufi')
        self.assertEqual(changeset.user_detail.contributor_blocks, 0)
        self.assertEqual(
            changeset.user_detail.contributor_since,
            datetime(2015, 1, 15)
            )
        self.assertEqual(changeset.user_detail.contributor_traces, 0)

        self.assertEqual(changeset.user_detail.nodes_c, 0)
        self.assertEqual(changeset.user_detail.nodes_m, 0)
        self.assertEqual(changeset.user_detail.nodes_d, 975)

        self.assertEqual(changeset.user_detail.ways_c, 0)
        self.assertEqual(changeset.user_detail.ways_m, 0)
        self.assertEqual(changeset.user_detail.ways_d, 43)

        self.assertEqual(changeset.user_detail.relations_c, 0)
        self.assertEqual(changeset.user_detail.relations_m, 0)
        self.assertEqual(changeset.user_detail.relations_d, 1)

        self.assertEqual(changeset.user_detail.changesets_no, 1)
        self.assertEqual(changeset.user_detail.changesets_changes, 1019)
        self.assertEqual(
            changeset.user_detail.changesets_f_tstamp,
            datetime(2015, 5, 25, 16, 30, 43)
            )
        self.assertEqual(
            changeset.user_detail.changesets_l_tstamp,
            datetime(2015, 5, 25, 16, 30, 43)
            )
        self.assertEqual(changeset.user_detail.changesets_mapping_days, '2015=1')


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
