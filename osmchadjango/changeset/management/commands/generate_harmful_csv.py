from django.core.management.base import BaseCommand
from ...models import Changeset, UserWhitelist, SuspicionReasons, SuspiciousFeature
from ...filters import ChangesetFilter
from djqscsv import write_csv

class Command(BaseCommand):
    help = 'Generate a CSV of all the harmful changesets from the database.'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        filename = options['filename'][0]
        qset = Changeset.objects.filter(harmful=True).select_related('user_detail')
        with open(filename, 'w') as csv_file:
          write_csv(qset, csv_file)

        self.stdout.write('done')