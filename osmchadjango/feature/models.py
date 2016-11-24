from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from ..users.models import User
import json
import codecs

class Feature(models.Model):

    user_detail = models.ForeignKey('changeset.UserDetail', blank=True, null=True)
    
    changeset = models.ForeignKey('changeset.Changeset')
    osm_id = models.IntegerField()
    osm_type = models.CharField(max_length=1000)
    osm_version = models.IntegerField()
    geometry = models.GeometryField(null=True, blank=True)
    oldGeometry = models.GeometryField(null=True, blank=True)
    geojson = JSONField()
    oldGeojson = JSONField(null=True, blank=True)
    reasons = models.ManyToManyField(
        'changeset.SuspicionReasons', related_name='features')
    harmful = models.NullBooleanField()
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(User, null=True, blank=True)
    check_date = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    url = models.SlugField(max_length=1000)
    comparator_version = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ('changeset', 'osm_id', 'osm_type',)

    def __str__(self):
        return '%s' % self.osm_id

    def osm_link(self):
        """Return the link to the changeset page on OSM website."""
        return 'http://www.openstreetmap.org/%s/%s' % (self.osm_type, self.osm_id, )

    @property
    def all_tags(self):
        geojson = self.geojson
        tags = []
        for key, value in geojson['properties'].iteritems():
            record = {}
            record["tag"] = key
            record["Value"] =  value
            tags.append(record)
        return tags

    @property
    def diff_tags(self):
        geojson = self.geojson
        oldGeojson = self.oldGeojson
        modified_tags = []
        deleted_tags = []
        added_tags = []
        unmodified_tags = []
        tags = {}
        for key, value in oldGeojson['properties'].iteritems():
            if 'osm:' not in key:
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
                    record["Value"] =  value
                    deleted_tags.append(record)

        for key, value in geojson['properties'].iteritems():
            if 'osm:' not in key:
                if key not in oldGeojson['properties']:
                    record = {}
                    record["tag"] = key
                    record["Value"] = value
                    added_tags.append(record)

        tags["modified"] = modified_tags
        tags["deleted"] = deleted_tags
        tags["added"] = added_tags
        tags["unmodified"] = unmodified_tags
        return tags