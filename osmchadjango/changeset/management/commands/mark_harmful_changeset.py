from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Changeset
from ....users.models import User


class Command(BaseCommand):
    help = 'Marks a list of changesets as harmful'

    def add_arguments(self, parser):
        parser.add_argument('check_username', nargs='+', type=str)
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        check_username = options['check_username'][0]
        check_user = User.objects.filter(username=check_username)
        if check_user:
            check_user = check_user[0]
            filename = options['filename'][0]
            fr = open(filename, 'r')
            for line in fr:
                changeset_id = line.rstrip()
                try:
                    changeset = Changeset.objects.get(id=changeset_id)
                    changeset.checked = True
                    changeset.harmful = True
                    changeset.check_user = check_user
                    changeset.check_date = timezone.now()
                    changeset.save()
                except:
                    pass
            fr.close()
