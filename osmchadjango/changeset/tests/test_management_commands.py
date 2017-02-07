from tempfile import mkdtemp
from os.path import join, exists
from shutil import rmtree
from csv import reader

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from .modelfactories import HarmfulChangesetFactory, SuspectChangesetFactory


class TestHarmfulCSV(TestCase):
    def setUp(self):
        self.dir = mkdtemp()
        self.csv = join(self.dir, 'test.csv')
        SuspectChangesetFactory()
        self.changeset = HarmfulChangesetFactory()
        self.out = StringIO()
        call_command('generate_harmful_csv', self.csv, stdout=self.out)

    def test_csv_creation(self):
        self.assertTrue(exists(self.csv))
        csv = reader(open(self.csv, 'r'))
        csv_rows = [row for row in csv]
        self.assertEqual(len(csv_rows), 2)
        self.assertEqual(csv_rows[1][0], str(self.changeset.id))
        self.assertIn(
            'File {} created.'.format(self.csv),
            self.out.getvalue()
            )

    def tearDown(self):
        rmtree(self.dir)
