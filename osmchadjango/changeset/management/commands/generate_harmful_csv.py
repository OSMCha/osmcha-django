from django.core.management.base import BaseCommand

from djqscsv import write_csv

from ...models import Changeset


class Command(BaseCommand):
    help = 'Generate a CSV of all the harmful changesets from the database.'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        filename = options['filename'][0]
        qset = Changeset.objects.filter(
            harmful=True
            ).select_related('user_detail').values(
            'id', 'user', 'editor', 'powerfull_editor', 'comment', 'source',
            'imagery_used', 'date', 'reasons', 'reasons__name', 'create',
            'modify', 'delete', 'bbox', 'is_suspect', 'harmful', 'checked',
            'check_user', 'check_date'
            )
        with open(filename, 'wb') as csv_file:
            write_csv(qset, csv_file)

        self.stdout.write('File {} created.'.format(filename))
