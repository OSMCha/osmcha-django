from django.core.management.base import BaseCommand

from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = """Deletes all user Tokens."""

    def handle(self, *args, **options):
        Token.objects.all().delete()
        self.stdout.write('All user Tokens were deleted.')
