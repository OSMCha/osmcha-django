from django.core.management.base import BaseCommand
from ...models import Changeset, UserWhitelist, SuspicionReasons, SuspiciousFeature
from ...filters import ChangesetFilter
from djqscsv import write_csv

class Command(BaseCommand):
    help = 'Generate a CSV of all the harmful changesets from the database.'

    def handle(self, *args, **options):
        qset = Changeset.objects.filter(harmful=True).select_related('user_detail')
        with open('harmful_changesets.csv', 'w') as csv_file:
          write_csv(qset, csv_file)

        self.stdout.write('done')