from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Changeset
from ....feature.models import Feature


def get_six_months_ago():
    return timezone.now() - timezone.timedelta(days=180)


class Command(BaseCommand):
    help = """Command to delete all the unchecked changesets older than 180 days.
    """

    def handle(self, *args, **options):
        date = get_six_months_ago
        Feature.objects.filter(
            changeset__date__lt=date(),
            changeset__checked=False,
            checked=False
            ).delete()
        Changeset.objects.filter(
            date__lt=date(),
            checked=False,
            features=None
            ).delete()
