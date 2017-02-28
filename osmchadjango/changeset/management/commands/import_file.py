from django.core.management.base import BaseCommand
from django.conf import settings

from osmcha.changeset import ChangesetList

from ...tasks import create_changeset


class Command(BaseCommand):
    help = """Read a local file and import all changesets."""

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        filename = options['filename'][0]
        cl = ChangesetList(filename, geojson=settings.CHANGESETS_FILTER)
        imported = [create_changeset(c['id']) for c in cl.changesets]

        self.stdout.write(
            '{} changesets created from {}.'.format(len(imported), filename)
            )
