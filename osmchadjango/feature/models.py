from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from ..users.models import User


class Feature(models.Model):
    changeset = models.ForeignKey(
        'changeset.Changeset', on_delete=models.CASCADE, related_name='features'
        )
    osm_id = models.BigIntegerField()
    osm_type = models.CharField(max_length=1000)
    osm_version = models.IntegerField()
    geometry = models.GeometryField(null=True, blank=True)
    old_geometry = models.GeometryField(null=True, blank=True)
    geojson = JSONField()
    old_geojson = JSONField(null=True, blank=True)
    reasons = models.ManyToManyField(
        'changeset.SuspicionReasons', related_name='features')
    tags = models.ManyToManyField(
        'changeset.Tag', related_name='features')
    harmful = models.NullBooleanField(db_index=True)
    checked = models.BooleanField(default=False, db_index=True)
    check_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True
        )
    check_date = models.DateTimeField(null=True, blank=True, db_index=True)
    url = models.SlugField(max_length=1000, db_index=True)
    comparator_version = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ('changeset', 'osm_id', 'osm_type',)
        ordering = ['-changeset_id']

    def __str__(self):
        return '{} {} v{}'.format(self.osm_type, self.osm_id, self.osm_version)

    def osm_link(self):
        """Return the link to the feature page on OSM website."""
        return 'https://www.openstreetmap.org/%s/%s' % (self.osm_type, self.osm_id)

    @property
    def all_tags(self):
        geojson = self.geojson
        tags = []
        for key, value in geojson['properties'].items():
            record = {}
            record["tag"] = key
            record["Value"] = value
            tags.append(record)
        return tags

    @property
    def diff_tags(self):
        geojson = self.geojson
        old_geojson = self.old_geojson
        modified_tags = []
        deleted_tags = []
        added_tags = []
        unmodified_tags = []
        tags = {}
        if old_geojson and old_geojson['properties']:
            old_props = old_geojson['properties']
        else:
            old_props = {}
        for key, value in old_props.items():
            if 'osm:' not in key and 'result:' not in key:
                if key in geojson['properties']:
                    record = {}
                    record["tag"] = key
                    record["oldValue"] = value
                    record["newValue"] = geojson['properties'][key]
                    if value != geojson['properties'][key]:
                        modified_tags.append(record)
                    else:
                        unmodified_tags.append(record)
                else:
                    record = {}
                    record["tag"] = key
                    record["Value"] = value
                    deleted_tags.append(record)

        for key, value in geojson['properties'].items():
            if 'osm:' not in key and 'result:' not in key:
                if key not in old_props:
                    record = {}
                    record["tag"] = key
                    record["Value"] = value
                    added_tags.append(record)

        tags["modified"] = modified_tags
        tags["deleted"] = deleted_tags
        tags["added"] = added_tags
        tags["unmodified"] = unmodified_tags
        return tags
