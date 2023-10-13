import json

from django.core.management.base import BaseCommand
from django.db import transaction

from osmchadjango.changeset.models import Changeset


class Command(BaseCommand):
    help = """Convert the features of the changesets to the new JSONField
        format. The changesets will be filtered according to the informed start
        and end dates.
        """

    def add_arguments(self, parser):
        parser.add_argument("start_date", nargs="+", type=str)
        parser.add_argument("end_date", nargs="+", type=str)

    def handle(self, *args, **options):
        start_date = options["start_date"][0]
        end_date = options["end_date"][0]
        migrate_features(start_date, end_date)


def filtered_json(feature):
    PRIMARY_TAGS = [
        "aerialway",
        "aeroway",
        "amenity",
        "barrier",
        "boundary",
        "building",
        "craft",
        "emergency",
        "geological",
        "highway",
        "historic",
        "landuse",
        "leisure",
        "man_made",
        "military",
        "natural",
        "office",
        "place",
        "power",
        "public_transport",
        "railway",
        "route",
        "shop",
        "tourism",
        "waterway",
    ]
    data = {
        "osm_id": feature.osm_id,
        "url": f"{feature.osm_type}-{feature.osm_id}",
        "version": feature.osm_version,
        "reasons": [reason.id for reason in feature.reasons.all()],
    }

    try:
        json_data = json.loads(feature.geojson)
        if "properties" in json_data.keys():
            properties = json_data.get("properties")
            if "name" in properties.keys():
                data["name"] = properties.get("name")

            [
                properties.pop(key)
                for key in list(properties.keys())
                if key not in PRIMARY_TAGS
            ]
            data["primary_tags"] = properties
    except TypeError:
        if "properties" in feature.geojson.keys():
            properties = feature.geojson["properties"]
            if "name" in properties.keys():
                data["name"] = properties["name"]

            [
                properties.pop(key)
                for key in list(properties.keys())
                if key not in PRIMARY_TAGS
            ]
            data["primary_tags"] = properties

    return data


def migrate_features(start_date, end_date):
    # last_changeset_date = Changeset.objects.order_by('-date')[0].date
    changesets = (
        Changeset.objects.filter(
            features__isnull=False,
            date__gte=start_date,
            date__lte=end_date,
            new_features=[],
        )
        .prefetch_related("features")
        .order_by("id")
        .distinct()
    )
    changeset_count = changesets.count()
    migrated = 0
    print(f"{changesets.count()} changesets to migrate")
    while migrated < changeset_count:
        with transaction.atomic():
            for changeset in changesets[migrated : migrated + 1000]:
                new_features_data = [
                    filtered_json(feature) for feature in changeset.features.all()
                ]
                changeset.new_features = new_features_data
                changeset.save(update_fields=["new_features"])
        print(f"{migrated}-{(migrated + 1000)} changesets migrated")
        migrated += 1000
