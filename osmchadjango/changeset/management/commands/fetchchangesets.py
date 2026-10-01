import socket

from django.core.management.base import BaseCommand

from ...tasks import fetch_latest, TIMEOUT


class Command(BaseCommand):
    help = """Command to import all the replication files since the last import
    or the last 1000."""

    def handle(self, *args, **options):
        # osmcha downloads replication files with urlretrieve, which has no
        # timeout parameter but honors the socket default.
        socket.setdefaulttimeout(TIMEOUT)
        fetch_latest()
