from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

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
            origin_reason = SuspicionReasons.objects.get(
                id=options['reason_1'][0]
                )
            final_reason = SuspicionReasons.objects.get(
                id=options['reason_2'][0]
                )
            changesets = origin_reason.changesets.exclude(reasons=final_reason)
            excluded_changesets = final_reason.changesets.filter(
                reasons=final_reason
                )
            changeset_number = changesets.count()
            origin_reason_name = origin_reason.name
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE changeset_changeset_reasons
                        SET suspicionreasons_id=%s
                        WHERE suspicionreasons_id=%s AND changeset_id not in %s
                    """,
                    [
                        final_reason.id,
                        origin_reason.id,
                        tuple([c.id for c in excluded_changesets])
                    ]
                    )
            origin_reason.delete()
            self.stdout.write(
                """{} changesets were moved from '{}' to '{}' SuspicionReasons.
                '{}' has been successfully deleted.
                """.format(
                    changeset_number, origin_reason_name, final_reason.name,
                    origin_reason_name
                    )
                )
        except SuspicionReasons.DoesNotExist:
            self.stdout.write(
                """Verify the SuspicionReasons ids.
                One or both of them does not exist.
                """
                )
