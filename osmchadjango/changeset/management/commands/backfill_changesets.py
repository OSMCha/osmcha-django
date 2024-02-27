from datetime import date

from django.core.management.base import BaseCommand

from ...models import Changeset
from ...tasks import create_changeset


class Command(BaseCommand):
    help = """Backfill missing changesets in a date range.
        Start and end dates should be in YYYY-MM-DD format."""

    def add_arguments(self, parser):
        parser.add_argument("start_date", nargs=1, type=str)
        parser.add_argument("end_date", nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            end_date = date.fromisoformat(options["end_date"][0])
        except (ValueError, TypeError):
            end_date = date.today()

        cl = Changeset.objects.filter(
            date__gte=date.fromisoformat(options["start_date"][0]),
            date__lte=end_date
        ).values_list('id')
        cl = [c[0] for c in cl]

        id = cl[len(cl) - 1]
        final = cl[0]
        while id < final:
            if id not in cl:
                create_changeset(id)
            id = id + 1
