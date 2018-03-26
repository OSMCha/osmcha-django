from django.core.management.base import BaseCommand
from django.conf import settings

from ...models import SuspicionReasons


class Command(BaseCommand):
    help = """Merge two SuspicionReasons. All the changesets associated with the
        first Reason will be moved to the second one and the first
        SuspicionReason will be deleted.
        """

    def add_arguments(self, parser):
        parser.add_argument('reason_1', nargs=1, type=str)
        parser.add_argument('reason_2', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            reason_1 = SuspicionReasons.objects.get(id=options['reason_1'][0])
            reason_2 = SuspicionReasons.objects.get(id=options['reason_2'][0])
            changesets = reason_1.changesets.exclude(reasons=reason_2)
            changeset_number = changesets.count()
            reason_1_name = reason_1.name
            for c in changesets:
                reason_2.changesets.add(c)
            reason_1.delete()
            self.stdout.write(
                """{} changesets were moved from '{}' to '{}' SuspicionReasons.
                '{}' has been successfully deleted.
                """.format(
                    changeset_number, reason_1_name, reason_2.name, reason_1_name
                    )
                )
        except SuspicionReasons.DoesNotExist:
            self.stdout.write(
                """Verify the SuspicionReasons ids.
                One or both of them does not exist.
                """
                )
