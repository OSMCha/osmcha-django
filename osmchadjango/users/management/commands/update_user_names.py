from django.core.management.base import BaseCommand

from ...utils import update_user_name
from ...models import User


class Command(BaseCommand):
    help = """Update the name field of all users with they current username in
    OSM."""

    def handle(self, *args, **options):
        [update_user_name(user) for user in User.objects.all()]
        print('Usernames updated.')
