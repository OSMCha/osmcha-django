from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Changeset
from ...tasks import create_changeset


def midnight(d):
    return timezone.make_aware(datetime.combine(d, time()))


class Command(BaseCommand):
    help = """Backfill missing changesets in a date range.
        Start and end dates should be in YYYY-MM-DD format."""

    def add_arguments(self, parser):
        parser.add_argument("--start_date", type=str)
        parser.add_argument("--end_date", type=str)

    def handle(self, *args, **options):
        # if start_date is not defined, set it as yesterday
        try:
            start_date = midnight(date.fromisoformat(options["start_date"]))
        except (ValueError, TypeError):
            start_date = midnight(date.today() - timedelta(days=1))
        # if end_date is not defined, set it as now
        try:
            end_date = midnight(date.fromisoformat(options["end_date"]))
        except (ValueError, TypeError):
            end_date = timezone.now()

        cl = Changeset.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).values_list("id")
        cl = [c[0] for c in cl]

        id = cl[len(cl) - 1]
        final = cl[0]
        while id < final:
            if id not in cl:
                try:
                    create_changeset(id)
                except Exception as e:
                    self.stdout.write("Failed to import changeset {}: {}".format(id, e))
            id = id + 1
