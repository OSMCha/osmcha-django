from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from ..users.models import User
import json
import codecs

class Feature(models.Model):

    user_detail = models.ForeignKey('changeset.UserDetail', blank=True, null=True)
    
    changeset = models.ForeignKey('changeset.Changeset')
    geometry = models.GeometryField()
    geojson = JSONField()
    reasons = models.ManyToManyField(
        'changeset.SuspicionReasons', related_name='features')
    harmful = models.NullBooleanField()
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(User, null=True, blank=True)
    check_date = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
 
    def __str__(self):
        return '%s' % self.id

    @classmethod
    def decode_string(value):
        return codecs.decode(value, 'unicode-escape')

    @property
    def geojson_obj(self):
        return json.loads((self.geojson).replace('osm:', 'osm_'))

    @property
    def diff_tags(self):
        geojson = json.loads((self.geojson))
        modified_tags = []
        deleted_tags = []
        tags = {}
        for key, value in geojson['properties']['oldVersion']['properties'].iteritems():
            if key in geojson['properties']:
                if value != geojson['properties'][key]:
                    record = {}
                    record["tag"] = key
                    record["oldValue"] = value
                    record["newValue"] = geojson['properties'][key]
                    modified_tags.append(record)
            else:
                record = {}
                record["tag"] = key
                record["Value"] =  value
                deleted_tags.append(record)

        tags["modified"] = modified_tags
        tags["deleted"] = deleted_tags
        return tags