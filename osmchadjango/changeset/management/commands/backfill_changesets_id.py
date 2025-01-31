from django.core.management.base import BaseCommand
from ...models import Changeset
from ...tasks import create_changeset


class Command(BaseCommand):
    help = "Backfill missing changesets from a given start ID."

    def add_arguments(self, parser):
        parser.add_argument("--start_id", type=int, required=True)

    def handle(self, *args, **options):
        latest_id = Changeset.objects.order_by("-id").values_list("id", flat=True).first()
        if not latest_id:
            return self.stdout.write("No changesets found.")

        for cid in range(options["start_id"], latest_id + 1):
            if not Changeset.objects.filter(id=cid).exists():
                try:
                    create_changeset(cid)
                    self.stdout.write(f"Imported {cid}")
                except Exception as e:
                    self.stdout.write(f"Failed {cid}: {e}")
                    