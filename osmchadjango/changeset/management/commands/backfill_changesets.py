from datetime import date, datetime, timedelta
from django.utils.timezone import make_aware, get_default_timezone

from django.core.management.base import BaseCommand

from ...models import Changeset
from ...tasks import create_changeset


class Command(BaseCommand):
    help = """Backfill missing changesets in a date range.
        Start and end dates should be in YYYY-MM-DD format."""

    def add_arguments(self, parser):
        parser.add_argument("--start_date", type=str)
        parser.add_argument("--end_date", type=str)

    def handle(self, *args, **options):
        # if start_date is not defined, set it as yesterday
        try:
            start_date = datetime.strptime(options["start_date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            start_date = datetime.now() - timedelta(days=1)

        # if end_date is not defined, set it as today
        try:
            end_date = datetime.strptime(options["end_date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            end_date = datetime.now()

        # Convert to timezone-aware datetime
        start_date = make_aware(start_date, timezone=get_default_timezone())
        end_date = make_aware(end_date, timezone=get_default_timezone())

        # Query the Changeset table using timezone-aware datetimes
        cl = Changeset.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).values_list("id", flat=True)

        if not cl:
            self.stdout.write("No missing changesets found in the given date range.")
            return

        id = max(cl)  # Last ID in the list
        final = min(cl)  # First ID in the list

        while id >= final:
            if id not in cl:
                try:
                    create_changeset(id)
                except Exception as e:
                    self.stdout.write(f"Failed to import changeset {id}: {e}")
            id -= 1
            