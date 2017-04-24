from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from ..models import Changeset


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
