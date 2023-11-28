from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Changeset


def get_six_months_ago():
    return timezone.now() - timezone.timedelta(days=180)


class Command(BaseCommand):
    help = """Command that deletes all the unchecked changesets older than 180 days.
    """

    def handle(self, *args, **options):
        date = get_six_months_ago
        Changeset.objects.filter(date__lt=date(), checked=False).delete()
