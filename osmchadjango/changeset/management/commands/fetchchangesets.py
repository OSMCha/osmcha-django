from django.core.management.base import BaseCommand

from ...tasks import fetch_latest


class Command(BaseCommand):
    help = """Command to import all the replication files since the last import
    or the last 1000."""

    def handle(self, *args, **options):
        fetch_latest()
